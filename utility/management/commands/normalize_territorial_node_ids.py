import re
from django.core.management.base import BaseCommand
from django.db import transaction
from utility.models import Clan, SubClan, State, City
from utility.territory_codes import build_clan_node_prefix, get_node_type_code


class Command(BaseCommand):
    help = 'Normalizes all Clan and Sub-Clan/Road Territorial Node IDs in the database to PRD standard (e.g. NG/SS/AKI/ABAK/CLN/002/SB/001)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulate the update and output sample changes without modifying the database.'
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        self.stdout.write(self.style.NOTICE(f"=== Territorial Node ID Normalization (Dry Run: {dry_run}) ==="))

        # Preload all States and Cities in memory to prevent N+1 queries over remote DB
        self.stdout.write("Preloading state and LGA lookup dictionaries...")
        states_map = {
            s.id: s for s in State.objects.select_related('country', 'geo_political_zone').all()
        }
        cities_map = {
            c.id: c for c in City.objects.select_related('state', 'state__country', 'state__geo_political_zone').all()
        }
        self.stdout.write(f"Loaded {len(states_map)} States and {len(cities_map)} Cities/LGAs.")

        # 1. Update Clans
        self.stdout.write("Fetching clans...")
        clans_qs = list(Clan.objects.all().only('id', 'name', 'node_id', 'state_id', 'city_id', 'geo_political_zone_id', 'country_id'))
        clans_to_update = []
        clan_id_map = {}  # clan.id -> new_node_id

        for clan in clans_qs:
            current_nid = (clan.node_id or '').strip()
            if current_nid.startswith('NG/') and current_nid.count('/') >= 4:
                clan_id_map[clan.id] = current_nid
                continue

            st = states_map.get(clan.state_id)
            ct = cities_map.get(clan.city_id)
            if not st and ct and ct.state_id:
                st = states_map.get(ct.state_id)

            co = (st.country if st else None)
            gz = (st.geo_political_zone if st else None)

            m = re.search(r'(\d+)$', current_nid)
            seq = int(m.group(1)) if m else (clan.id or 1)

            if st:
                prefix = build_clan_node_prefix(co, gz, st, ct)
                new_clan_nid = f"{prefix}{seq:03d}"
            else:
                new_clan_nid = f"CLN-{seq:03d}"

            clan_id_map[clan.id] = new_clan_nid
            if current_nid != new_clan_nid:
                clan.node_id = new_clan_nid
                clans_to_update.append(clan)

        self.stdout.write(f"Clans to update: {len(clans_to_update)} / {len(clans_qs)}")
        if clans_to_update:
            sample = clans_to_update[0]
            self.stdout.write(f"Sample Clan update: '{sample.name}' -> {sample.node_id}")

        # 2. Update SubClans and Roads
        self.stdout.write("Fetching subclans...")
        subclans_qs = list(SubClan.objects.all().only('id', 'name', 'node_id', 'node_type', 'clan_id', 'parent_road_id'))
        subclans_to_update = []

        for sc in subclans_qs:
            current_nid = (sc.node_id or '').strip()
            if current_nid.startswith('NG/') and current_nid.count('/') >= 6:
                continue

            clan_nid = clan_id_map.get(sc.clan_id)
            if not clan_nid:
                clan_nid = "CLN-001"

            new_sc_nid = None

            # Check if current_nid has legacy clan prefix (CLN-xxx/... or NDD-CLN-xxx/...)
            m_legacy = re.match(r'^(?:[A-Z0-9]+-)?CLN-\d+/(.*)$', current_nid, re.IGNORECASE)
            if m_legacy:
                sub_path = m_legacy.group(1)
                # Normalize unnested street/close if needed
                if sc.node_type == 'STREET' and sub_path.startswith('STR') and '/MR/' not in sub_path:
                    m_s = re.match(r'^STR[-/]?(\d+)$', sub_path)
                    if m_s:
                        sub_path = f"MR/001/SR/001/STR/{int(m_s.group(1)):03d}"
                elif sc.node_type == 'CLOSE' and sub_path.startswith('CLS') and '/STR/' not in sub_path:
                    m_c = re.match(r'^CLS[-/]?(\d+)$', sub_path)
                    if m_c:
                        sub_path = f"MR/001/SR/001/STR/001/CLS/{int(m_c.group(1)):03d}"
                new_sc_nid = f"{clan_nid}/{sub_path}"
            elif current_nid.startswith(('MR/', 'SR/', 'STR/', 'CLS/', 'SB/')):
                new_sc_nid = f"{clan_nid}/{current_nid}"
            elif re.match(r'^(?:SB|MR|SR|STR|CLS)[-/]?(\d+)$', current_nid, re.IGNORECASE):
                code = get_node_type_code(sc.node_type)
                m_seq = re.search(r'(\d+)$', current_nid)
                seq = int(m_seq.group(1)) if m_seq else 1
                new_sc_nid = f"{clan_nid}/{code}/{seq:03d}"
            else:
                code = get_node_type_code(sc.node_type)
                m_seq = re.search(r'(\d+)$', current_nid)
                seq = int(m_seq.group(1)) if m_seq else (sc.id or 1)
                new_sc_nid = f"{clan_nid}/{code}/{seq:03d}"

            if new_sc_nid and new_sc_nid != current_nid:
                sc.node_id = new_sc_nid
                subclans_to_update.append(sc)

        self.stdout.write(f"Sub-Clans to update: {len(subclans_to_update)} / {len(subclans_qs)}")
        if subclans_to_update:
            sample_sc = subclans_to_update[0]
            self.stdout.write(f"Sample Sub-Clan update: '{sample_sc.name}' -> {sample_sc.node_id}")

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run completed. No changes written to database."))
            return

        with transaction.atomic():
            if clans_to_update:
                Clan.objects.bulk_update(clans_to_update, ['node_id'], batch_size=500)
                self.stdout.write(self.style.SUCCESS(f"Successfully committed {len(clans_to_update)} Clan node IDs!"))

            if subclans_to_update:
                SubClan.objects.bulk_update(subclans_to_update, ['node_id'], batch_size=500)
                self.stdout.write(self.style.SUCCESS(f"Successfully committed {len(subclans_to_update)} Sub-Clan node IDs!"))

        self.stdout.write(self.style.SUCCESS("All territorial node IDs normalized successfully!"))
