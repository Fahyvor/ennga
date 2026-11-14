import csv
import io
import re
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.db import transaction
from django.db.models import Q

from accounts.models import Profile
from utility.models import (
    Clan, SubClan, State, City, GeoPoliticalZone, Country,
    generate_territory_code, NODE_TYPE_CHOICES, ROAD_RELATION_CHOICES,
    ROAD_SURFACE_CHOICES, ROAD_CONDITION_CHOICES
)
from utility.territory_codes import (
    resolve_state, get_country_code, get_geo_zone_code,
    get_state_code, get_lga_code, build_clan_node_prefix,
    get_node_type_code, build_road_node_prefix
)
from platform_admin.views_clans import is_platform_admin, invalidate_clan_caches


NODE_TYPE_ALIASES = {
    'SUBCLAN': 'SUB_CLAN',
    'SUB_CLAN': 'SUB_CLAN',
    'SUB-CLAN': 'SUB_CLAN',
    'SB': 'SUB_CLAN',
    'COMMUNITY': 'COMMUNITY',
    'VILLAGE': 'COMMUNITY',
    'COM': 'COMMUNITY',
    'MAJOR_ROAD': 'MAJOR_ROAD',
    'MAJOR': 'MAJOR_ROAD',
    'MAJOR ROAD': 'MAJOR_ROAD',
    'MR': 'MAJOR_ROAD',
    'TRUNK': 'MAJOR_ROAD',
    'META_ROAD': 'META_ROAD',
    'META': 'META_ROAD',
    'SUB_ROAD': 'SUB_ROAD',
    'SUB ROAD': 'SUB_ROAD',
    'SUB': 'SUB_ROAD',
    'SR': 'SUB_ROAD',
    'LINK_ROAD': 'LINK_ROAD',
    'LINK ROAD': 'LINK_ROAD',
    'LINK': 'LINK_ROAD',
    'STREET': 'STREET',
    'STR': 'STREET',
    'ST': 'STREET',
    'CLOSE': 'CLOSE',
    'CLS': 'CLOSE',
    'CRESCENT': 'CLOSE',
    'CRES': 'CLOSE',
}


def normalize_node_type(val, default='SUB_CLAN'):
    if not val:
        return default
    clean = str(val).strip().upper().replace(' ', '_').replace('-', '_')
    return NODE_TYPE_ALIASES.get(clean, NODE_TYPE_ALIASES.get(str(val).strip().upper(), default))


def parse_uploaded_csv(uploaded_file):
    """
    Safely reads an uploaded CSV file, handling various encodings and delimiters.
    Returns (headers, rows_list, error_message).
    """
    try:
        content = uploaded_file.read()
    except Exception as e:
        return None, None, f"Failed to read file: {str(e)}"

    decoded = None
    for enc in ('utf-8-sig', 'utf-8', 'latin-1', 'cp1252'):
        try:
            decoded = content.decode(enc)
            break
        except UnicodeDecodeError:
            continue

    if decoded is None:
        return None, None, "Unable to decode file. Please ensure it is saved in UTF-8 or standard CSV format."

    # Detect delimiter: comma, semicolon, or tab
    sample = decoded[:4096]
    delimiter = ','
    if ';' in sample and sample.count(';') > sample.count(','):
        delimiter = ';'
    elif '\t' in sample and sample.count('\t') > sample.count(','):
        delimiter = '\t'

    f = io.StringIO(decoded)
    reader = csv.reader(f, delimiter=delimiter)
    try:
        raw_headers = next(reader)
    except StopIteration:
        return None, None, "The uploaded CSV file is empty."

    # Normalize headers
    headers = [re.sub(r'[^a-zA-Z0-9_]', '_', h.strip().lower()).strip('_') for h in raw_headers]

    rows = []
    for r_idx, r in enumerate(reader, start=2):
        if not r or not any(field.strip() for field in r):
            continue
        row_dict = {}
        for h_idx, h in enumerate(headers):
            val = r[h_idx].strip() if h_idx < len(r) else ''
            row_dict[h] = val
        row_dict['_row_num'] = r_idx
        rows.append(row_dict)

    if not rows:
        return None, None, "No valid data rows found in CSV."

    return headers, rows, None


def process_territorial_nodes_csv(
    rows,
    headers,
    default_state_id=None,
    default_city_id=None,
    node_type_override=None,
    auto_create_clans=True,
    dry_run=True,
    user=None
):
    """
    Core engine that processes parsed CSV rows for preview (dry_run=True) or database execution (dry_run=False).
    """
    user_profile = getattr(user, 'account_profile', None) if user else None

    # Resolve default state & city models
    default_state = None
    default_city = None
    if default_state_id:
        try:
            default_state = State.objects.filter(id=int(default_state_id), is_deleted=False).first()
        except (ValueError, TypeError):
            pass

    if default_city_id:
        try:
            default_city = City.objects.filter(id=int(default_city_id), is_deleted=False).first()
            if default_city and not default_state and default_city.state:
                default_state = default_city.state
        except (ValueError, TypeError):
            pass

    default_country = (
        (default_state.country if default_state else None)
        or Country.my_objects.first()
        or Country.objects.first()
    )
    default_geo_zone = (
        (default_state.geo_political_zone if default_state else None)
        or (default_city.state.geo_political_zone if default_city and default_city.state else None)
    )

    # In-memory tracking structures across the CSV batch
    clans_cache = {}          # (lga_key, clan_name.lower()) -> dict of clan metadata & object
    nodes_cache = {}          # (lga_key, clan_name.lower(), node_name.lower(), node_type) -> dict of node metadata & object
    allocated_seqs = {}       # prefix -> int sequence counter
    next_clan_seq_by_state = {}  # state_key -> sequential tracker for brand new clans created in this batch

    preview_rows = []
    total_valid = 0
    total_skipped = 0
    new_clans_planned = 0
    new_nodes_planned = 0

    valid_surface_choices = [c[0] for c in ROAD_SURFACE_CHOICES]
    valid_condition_choices = [c[0] for c in ROAD_CONDITION_CHOICES]
    valid_relation_choices = [c[0] for c in ROAD_RELATION_CHOICES]

    for row in rows:
        row_num = row.get('_row_num', 0)
        errors = []
        warnings = []

        # 1. Extract Clan Name
        clan_name = (
            row.get('clan') or row.get('clan_name') or row.get('parent_clan') or row.get('clans') or ''
        ).strip()
        if not clan_name:
            # Check first column if it might be clan
            if headers and headers[0] in ('clan', 'clans', 'clan_name'):
                clan_name = row.get(headers[0], '').strip()

        if not clan_name:
            preview_rows.append({
                'row_num': row_num,
                'clan_name': '(Missing)',
                'clan_node_id': '-',
                'name': row.get('name') or row.get('subclan') or '-',
                'node_type': 'SUB_CLAN',
                'node_type_display': 'Sub-Clan',
                'parent_name': '-',
                'generated_node_id': '-',
                'status': 'Error: Missing Clan name',
                'status_code': 'error',
                'is_valid': False
            })
            continue

        # 2. Extract Node Name and Determine Node Type
        name = ''
        node_type = 'SUB_CLAN'
        parent_road_name = ''

        if 'close' in row and row['close']:
            name = row['close'].strip()
            node_type = 'CLOSE'
            parent_road_name = (row.get('parent_road') or row.get('street') or row.get('parent') or '').strip()
        elif 'street' in row and row['street']:
            name = row['street'].strip()
            node_type = 'STREET'
            parent_road_name = (row.get('parent_road') or row.get('sub_road') or row.get('parent') or '').strip()
        elif 'sub_road' in row and row['sub_road']:
            name = row['sub_road'].strip()
            node_type = 'SUB_ROAD'
            parent_road_name = (row.get('parent_road') or row.get('major_road') or row.get('parent') or '').strip()
        elif 'major_road' in row and row['major_road']:
            name = row['major_road'].strip()
            node_type = 'MAJOR_ROAD'
            parent_road_name = (row.get('parent_road') or row.get('subclan') or row.get('community') or row.get('parent') or '').strip()
        elif 'community' in row and row['community']:
            name = row['community'].strip()
            node_type = 'COMMUNITY'
        elif 'subclan' in row and row['subclan']:
            name = row['subclan'].strip()
            node_type = 'SUB_CLAN'
        elif 'name' in row and row['name']:
            name = row['name'].strip()
            raw_type = row.get('node_type') or row.get('type') or node_type_override or 'SUB_CLAN'
            node_type = normalize_node_type(raw_type, default=node_type_override or 'SUB_CLAN')
            parent_road_name = (row.get('parent_road') or row.get('parent') or '').strip()
        else:
            # Look for 2nd column as node name
            candidate_cols = [c for c in headers if c not in ('clan', 'clan_name', 'parent_clan', 'state', 'city', 'lga')]
            if candidate_cols:
                col = candidate_cols[0]
                name = row.get(col, '').strip()
                node_type = normalize_node_type(node_type_override or col, default='SUB_CLAN')
                parent_road_name = (row.get('parent_road') or row.get('parent') or '').strip()

        if not name:
            preview_rows.append({
                'row_num': row_num,
                'clan_name': clan_name,
                'clan_node_id': '-',
                'name': '(Missing)',
                'node_type': node_type,
                'node_type_display': dict(NODE_TYPE_CHOICES).get(node_type, node_type),
                'parent_name': '-',
                'generated_node_id': '-',
                'status': 'Error: Missing territorial node name',
                'status_code': 'error',
                'is_valid': False
            })
            continue

        # 3. Road attributes (surface, condition, relation)
        road_surface = (row.get('road_surface') or row.get('surface') or 'ASPHALT').strip().upper()
        if road_surface not in valid_surface_choices:
            road_surface = 'ASPHALT'

        road_condition = (row.get('road_condition') or row.get('condition') or 'GOOD').strip().upper()
        if road_condition not in valid_condition_choices:
            road_condition = 'GOOD'

        road_relation = (row.get('road_relation') or row.get('relation') or '').strip().upper()
        if not road_relation or road_relation not in valid_relation_choices:
            if node_type in ('MAJOR_ROAD', 'META_ROAD'):
                road_relation = 'CONTAINED_SUBCLAN' if parent_road_name else 'CONTAINED_CLAN'
            else:
                road_relation = 'CONTAINED_CLAN'

        # 4. Resolve Target State & Target LGA (City) for this row
        row_state_val = (row.get('state') or row.get('state_name') or '').strip()
        st = resolve_state(row_state_val) if row_state_val else default_state

        row_city_val = (row.get('city') or row.get('lga') or row.get('city_name') or '').strip()
        ct = None
        if row_city_val:
            if st:
                ct = City.objects.filter(name__iexact=row_city_val, state=st, is_deleted=False).first()
            if not ct:
                ct = City.objects.filter(name__iexact=row_city_val, is_deleted=False).first()
        if not ct and default_city:
            ct = default_city

        if ct and not st and ct.state:
            st = ct.state

        gz = (st.geo_political_zone if st else None) or (ct.state.geo_political_zone if ct and ct.state else None) or default_geo_zone
        co = (st.country if st else None) or default_country

        lga_key = ct.id if ct else (row_city_val.lower() if row_city_val else 'no_lga')
        clan_cache_key = (lga_key, clan_name.lower())

        clan_info = clans_cache.get(clan_cache_key)

        if not clan_info:
            # Query existing Clan strictly scoped to the same LGA / City
            clan_qs = Clan.objects.filter(name__iexact=clan_name, is_deleted=False).select_related('city', 'state', 'country', 'geo_political_zone')
            clan_obj = None
            if ct:
                clan_obj = clan_qs.filter(city=ct).first()
            elif st:
                clan_obj = clan_qs.filter(Q(state=st) | Q(city__state=st)).first()
            else:
                clan_obj = clan_qs.first()

            if clan_obj:
                clan_info = {
                    'obj': clan_obj,
                    'is_new': False,
                    'name': clan_obj.name,
                    'node_id': clan_obj.display_node_id or clan_obj.node_id,
                    'state': clan_obj.state,
                    'city': clan_obj.city,
                    'country': clan_obj.country or default_country,
                    'geo_political_zone': clan_obj.geo_political_zone or default_geo_zone,
                }
                clans_cache[clan_cache_key] = clan_info
            else:
                # Clan does not exist yet in this specific LGA
                state_seq_key = st.id if st else 'no_state'
                if state_seq_key not in next_clan_seq_by_state:
                    if st:
                        existing_count = Clan.objects.filter(Q(state=st) | Q(city__state=st), is_deleted=False).count()
                    else:
                        existing_count = Clan.objects.filter(is_deleted=False).count()
                    next_clan_seq_by_state[state_seq_key] = existing_count
                next_clan_seq_by_state[state_seq_key] += 1
                next_seq = next_clan_seq_by_state[state_seq_key]

                if st:
                    c_prefix = build_clan_node_prefix(co, gz, st, ct)
                    new_clan_node_id = f"{c_prefix}{next_seq:03d}"
                else:
                    new_clan_node_id = f"CLN-{next_seq:03d}"

                code = generate_territory_code(clan_name)

                if not dry_run and auto_create_clans:
                    new_clan_obj = Clan.objects.create(
                        name=clan_name,
                        code=code,
                        node_id=new_clan_node_id,
                        state=st,
                        city=ct,
                        geo_political_zone=gz,
                        country=co
                    )
                    if user_profile:
                        new_clan_obj.managers.add(user_profile)

                    clan_info = {
                        'obj': new_clan_obj,
                        'is_new': True,
                        'name': clan_name,
                        'node_id': new_clan_obj.node_id,
                        'state': st,
                        'city': ct,
                        'country': co,
                        'geo_political_zone': gz,
                    }
                else:
                    clan_info = {
                        'obj': None,
                        'is_new': True,
                        'name': clan_name,
                        'node_id': new_clan_node_id,
                        'state': st,
                        'city': ct,
                        'country': co,
                        'geo_political_zone': gz,
                    }

                new_clans_planned += 1
                clans_cache[clan_cache_key] = clan_info

        # 5. Resolve Parent Road (if applicable, scoped to same LGA)
        parent_obj = None
        parent_nid = None
        parent_display = '-'

        if parent_road_name:
            parent_key = (lga_key, clan_name.lower(), parent_road_name.lower())
            if parent_key in nodes_cache:
                parent_data = nodes_cache[parent_key]
                parent_obj = parent_data.get('obj')
                parent_nid = parent_data.get('node_id')
                parent_display = f"{parent_road_name} [{parent_nid}]"
            else:
                db_parent_qs = SubClan.objects.filter(
                    name__iexact=parent_road_name,
                    is_deleted=False
                )
                if clan_info.get('obj'):
                    db_parent = db_parent_qs.filter(clan=clan_info['obj']).first()
                elif ct:
                    db_parent = db_parent_qs.filter(Q(city=ct) | Q(clan__city=ct), clan__name__iexact=clan_name).first()
                else:
                    db_parent = db_parent_qs.filter(clan__name__iexact=clan_name).first()

                if db_parent:
                    parent_obj = db_parent
                    parent_nid = db_parent.node_id or db_parent.display_node_id
                    parent_display = f"{db_parent.name} [{parent_nid}]"
                    nodes_cache[parent_key] = {'obj': db_parent, 'node_id': parent_nid, 'node_type': db_parent.node_type}
                else:
                    clan_nid = clan_info['node_id']
                    if node_type in ('MAJOR_ROAD', 'META_ROAD') and auto_create_clans:
                        sb_prefix = f"{clan_nid}/SB/"
                        if sb_prefix not in allocated_seqs:
                            existing_sbs = SubClan.objects.filter(node_id__startswith=sb_prefix).values_list('node_id', flat=True)
                            patt = re.compile(rf"^{re.escape(sb_prefix)}(\d+)")
                            m_seq = 0
                            for nid in existing_sbs:
                                if nid:
                                    m = patt.match(nid)
                                    if m:
                                        try:
                                            m_seq = max(m_seq, int(m.group(1)))
                                        except ValueError:
                                            pass
                            allocated_seqs[sb_prefix] = m_seq

                        allocated_seqs[sb_prefix] += 1
                        sb_node_id = f"{sb_prefix}{allocated_seqs[sb_prefix]:03d}"

                        if not dry_run and clan_info.get('obj'):
                            new_sb = SubClan.objects.create(
                                name=parent_road_name,
                                clan=clan_info['obj'],
                                node_type='SUB_CLAN',
                                node_id=sb_node_id,
                                city=clan_info.get('city'),
                                state=clan_info.get('state'),
                                geo_political_zone=clan_info.get('geo_political_zone'),
                                country=clan_info.get('country')
                            )
                            if user_profile:
                                new_sb.managers.add(user_profile)
                            parent_obj = new_sb
                        parent_nid = sb_node_id
                        parent_display = f"{parent_road_name} [{parent_nid}]"
                        nodes_cache[parent_key] = {'obj': parent_obj, 'node_id': sb_node_id, 'node_type': 'SUB_CLAN'}
                    else:
                        parent_display = f"{parent_road_name} (Unlinked - Not Found)"
                        warnings.append(f"Parent '{parent_road_name}' not found under '{clan_name}'.")

        # 6. Compute Node ID Prefix & Sequential ID
        clan_nid = clan_info['node_id']

        if node_type in ('SUB_CLAN', 'COMMUNITY'):
            prefix = f"{clan_nid}/SB/"
        elif node_type in ('MAJOR_ROAD', 'META_ROAD'):
            if parent_nid:
                prefix = f"{parent_nid}/MR/"
            else:
                prefix = f"{clan_nid}/MR/"
        elif node_type in ('SUB_ROAD', 'LINK_ROAD'):
            if parent_nid:
                prefix = f"{parent_nid}/SR/"
            else:
                prefix = f"{clan_nid}/MR/001/SR/"
        elif node_type == 'STREET':
            if parent_nid:
                prefix = f"{parent_nid}/STR/"
            else:
                prefix = f"{clan_nid}/MR/001/SR/001/STR/"
        elif node_type == 'CLOSE':
            if parent_nid:
                prefix = f"{parent_nid}/CLS/"
            else:
                prefix = f"{clan_nid}/MR/001/SR/001/STR/001/CLS/"
        else:
            type_code = get_node_type_code(node_type)
            prefix = f"{clan_nid}/{type_code}/"

        if prefix not in allocated_seqs:
            existing_nids = SubClan.objects.filter(node_id__startswith=prefix).values_list('node_id', flat=True)
            pattern = re.compile(rf"^{re.escape(prefix)}(\d+)")
            max_seq = 0
            for nid in existing_nids:
                if nid:
                    m = pattern.match(nid)
                    if m:
                        try:
                            s_val = int(m.group(1))
                            if s_val > max_seq:
                                max_seq = s_val
                        except ValueError:
                            pass
            allocated_seqs[prefix] = max_seq

        allocated_seqs[prefix] += 1
        generated_node_id = f"{prefix}{allocated_seqs[prefix]:03d}"

        # 7. Check for Duplicate Existence in Database (strictly scoped to the SAME LGA)
        is_existing = False
        target_lga = ct or (clan_info['obj'].city if clan_info.get('obj') else None)

        # Check A: Duplicate row within the same CSV batch in the SAME LGA
        node_batch_key = (lga_key, clan_name.lower(), name.lower(), node_type)
        if node_batch_key in nodes_cache and nodes_cache[node_batch_key].get('seen_in_batch'):
            is_existing = True
            existing_info = nodes_cache[node_batch_key]
            generated_node_id = existing_info.get('node_id', generated_node_id)
        else:
            # Check B: Check in Database for existing node strictly in the SAME LGA
            existing_qs = SubClan.objects.filter(
                name__iexact=name,
                node_type=node_type,
                is_deleted=False
            )
            if clan_info.get('obj'):
                existing_qs = existing_qs.filter(clan=clan_info['obj'])
            if target_lga:
                existing_qs = existing_qs.filter(Q(city=target_lga) | Q(clan__city=target_lga))

            existing_node = existing_qs.first()
            if existing_node:
                is_existing = True
                generated_node_id = existing_node.node_id or existing_node.display_node_id

        resolved_lga_name = ct.name if ct else (row_city_val or getattr(clan_info.get('city'), 'name', '-'))
        resolved_state_name = st.name if st else (row_state_val or getattr(clan_info.get('state'), 'name', '-'))

        # 8. Commit to Database if not dry_run
        status_msg = ""
        status_code = ""

        if is_existing:
            lga_suffix = f" in {resolved_lga_name}" if resolved_lga_name and resolved_lga_name != '-' else ""
            status_msg = f"Already exists{lga_suffix} ({generated_node_id}) - skipped"
            status_code = "existing"
            total_skipped += 1
        elif dry_run:
            if clan_info['is_new']:
                status_msg = "New Clan will be registered & Node created"
                status_code = "ready_new_clan"
            else:
                status_msg = "Ready to create"
                status_code = "ready"
            total_valid += 1
            new_nodes_planned += 1
        else:
            # Execution mode
            try:
                subclan_obj = SubClan.objects.create(
                    name=name,
                    clan=clan_info['obj'],
                    node_type=node_type,
                    node_id=generated_node_id,
                    parent_road=parent_obj,
                    road_relation=road_relation,
                    road_surface=road_surface,
                    road_condition=road_condition,
                    city=clan_info.get('city'),
                    state=clan_info.get('state'),
                    geo_political_zone=clan_info.get('geo_political_zone'),
                    country=clan_info.get('country')
                )
                if user_profile:
                    subclan_obj.managers.add(user_profile)

                status_msg = "Created successfully"
                status_code = "created"
                total_valid += 1
                new_nodes_planned += 1
            except Exception as e:
                status_msg = f"Failed to save: {str(e)}"
                status_code = "error"

        # Register in in-memory nodes_cache so subsequent rows in same CSV recognize it
        if not is_existing:
            nodes_cache[node_batch_key] = {
                'obj': subclan_obj if not dry_run and 'subclan_obj' in locals() else None,
                'node_id': generated_node_id,
                'node_type': node_type,
                'seen_in_batch': True
            }
            parent_reg_key = (lga_key, clan_name.lower(), name.lower())
            nodes_cache[parent_reg_key] = {
                'obj': subclan_obj if not dry_run and 'subclan_obj' in locals() else None,
                'node_id': generated_node_id,
                'node_type': node_type
            }

        # Append row to results
        preview_rows.append({
            'row_num': row_num,
            'clan_name': clan_name,
            'clan_status': 'new' if clan_info['is_new'] else 'existing',
            'clan_node_id': clan_info['node_id'],
            'name': name,
            'lga_name': resolved_lga_name,
            'state_name': resolved_state_name,
            'node_type': node_type,
            'node_type_display': dict(NODE_TYPE_CHOICES).get(node_type, node_type),
            'parent_name': parent_display,
            'road_relation': road_relation,
            'road_surface': road_surface,
            'road_condition': road_condition,
            'generated_node_id': generated_node_id,
            'status': status_msg,
            'status_code': status_code,
            'is_valid': (status_code != 'error'),
            'warnings': warnings
        })

    return {
        'total_rows': len(preview_rows),
        'valid_rows': total_valid,
        'skipped_rows': total_skipped,
        'new_clans_count': new_clans_planned,
        'new_nodes_count': new_nodes_planned,
        'rows': preview_rows,
    }


@login_required
def territorial_nodes_import_csv_view(request):
    """
    Handles both AJAX dry-run preview and atomic database execution of territorial nodes CSV.
    Supports Sub-Clans, Major Roads, Sub Roads, Streets, and Closes.
    """
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('is_ajax') == 'true'

    if request.method == "POST":
        csv_file = request.FILES.get('csv_file')
        if not csv_file:
            msg = "Please select a valid CSV file to upload."
            if is_ajax:
                return JsonResponse({'status': 'error', 'message': msg}, status=400)
            messages.error(request, msg)
            return redirect(request.POST.get('next') or 'platform_admin:road-list')

        # Read & Parse CSV content
        headers, rows, error = parse_uploaded_csv(csv_file)
        if error:
            if is_ajax:
                return JsonResponse({'status': 'error', 'message': error}, status=400)
            messages.error(request, error)
            return redirect(request.POST.get('next') or 'platform_admin:road-list')

        action = request.POST.get('action', 'preview').strip().lower()
        is_dry_run = (action == 'preview')
        default_state_id = request.POST.get('default_state')
        default_city_id = request.POST.get('default_city')
        node_type_override = request.POST.get('node_type_override')
        if node_type_override == 'AUTO' or not node_type_override:
            node_type_override = None

        auto_create_clans = request.POST.get('auto_create_clans') in ('true', '1', 'on', True)

        try:
            if is_dry_run:
                # Dry Run Mode: compute IDs and validate without writing to DB
                result = process_territorial_nodes_csv(
                    rows=rows,
                    headers=headers,
                    default_state_id=default_state_id,
                    default_city_id=default_city_id,
                    node_type_override=node_type_override,
                    auto_create_clans=auto_create_clans,
                    dry_run=True,
                    user=request.user
                )
                return JsonResponse({
                    'status': 'success',
                    'action': 'preview',
                    **result
                })
            else:
                # Commit Mode: Atomic database transaction
                with transaction.atomic():
                    result = process_territorial_nodes_csv(
                        rows=rows,
                        headers=headers,
                        default_state_id=default_state_id,
                        default_city_id=default_city_id,
                        node_type_override=node_type_override,
                        auto_create_clans=auto_create_clans,
                        dry_run=False,
                        user=request.user
                    )
                    invalidate_clan_caches()

                success_msg = (
                    f"Successfully imported {result['new_nodes_count']} territorial node(s)! "
                    f"({result['new_clans_count']} new Clan(s) registered, {result['skipped_rows']} existing skipped)."
                )

                if is_ajax:
                    return JsonResponse({
                        'status': 'success',
                        'action': 'commit',
                        'message': success_msg,
                        **result
                    })
                messages.success(request, success_msg)
                return redirect(request.POST.get('next') or 'platform_admin:road-list')

        except Exception as e:
            err_msg = f"Error processing CSV: {str(e)}"
            if is_ajax:
                return JsonResponse({'status': 'error', 'message': err_msg}, status=500)
            messages.error(request, err_msg)
            return redirect(request.POST.get('next') or 'platform_admin:road-list')

    # If GET, redirect back to list
    return redirect('platform_admin:road-list')
