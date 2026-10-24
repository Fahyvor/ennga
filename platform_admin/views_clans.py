import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from django.db.models import Q, Count, Prefetch
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.urls import reverse
from django.core.cache import cache

from accounts.models import Account, Profile
from utility.models import (
    Clan, SubClan, State, City, GeoPoliticalZone, Country,
    NODE_TYPE_CHOICES, ROAD_RELATION_CHOICES, ROAD_SURFACE_CHOICES, ROAD_CONDITION_CHOICES,
    INFRASTRUCTURE_TYPE_CHOICES, INFRASTRUCTURE_STATUS_CHOICES, SIDE_OF_ROAD_CHOICES,
    TerritorialInfrastructure
)
from platform_admin.models import Historical, MarketSector, GeoPhysicalData
from utility.territory_codes import resolve_state
from .forms_clan import ClanForm, SubClanForm, TerritorialInfrastructureForm


def is_platform_admin(user):
    return user.is_authenticated and (user.is_admin or user.is_staff or user.is_superuser)


def can_user_manage_clan(user, clan):
    """
    Returns True if user has access to modify the clan,
    add sub-clans to it, or input/modify its data.
    """
    if not user.is_authenticated:
        return False
    if is_platform_admin(user):
        return True
    if hasattr(user, 'account_profile'):
        profile = user.account_profile
        if profile in clan.restricted_users.all():
            return False
        if profile in clan.managers.all():
            return True
        if clan.city and profile in clan.city.managers.all():
            return True
    return False


def can_user_manage_subclan(user, subclan):
    if not user.is_authenticated:
        return False
    if is_platform_admin(user):
        return True
    if subclan.clan and can_user_manage_clan(user, subclan.clan):
        return True
    if hasattr(user, 'account_profile'):
        profile = user.account_profile
        if profile in subclan.restricted_users.all():
            return False
        if profile in subclan.managers.all():
            return True
        if subclan.city and profile in subclan.city.managers.all():
            return True
    return False


def invalidate_clan_caches():
    cache.delete_many([
        'kpi_total_clans',
        'kpi_total_subclans',
        'kpi_total_pure_subclans',
        'kpi_subclan_type_count',
        'kpi_community_type_count',
        'kpi_total_roads',
        'kpi_major_roads_count',
        'kpi_sub_roads_count',
        'kpi_streets_count',
        'kpi_closes_count',
        'dropdown_all_clans',
        'dropdown_all_clans_simple',
        'dropdown_all_subclans_simple',
        'all_states_annotated',
        'all_states_list',
        'all_states_simple',
        'all_geo_zones_list',
    ])



@login_required
def clan_list_view(request):
    """
    Directory & listing of all Clans with search, state filtering,
    view modes ('all', 'my', 'subclans'), and pagination.
    """
    query = request.GET.get('q', '').strip()
    state_id = request.GET.get('state', '').strip()
    view_mode = request.GET.get('view_mode', 'all')
    node_type_filter = request.GET.get('node_type', '').strip()
    page = request.GET.get('page', 1)

    user_profile = getattr(request.user, 'account_profile', None)
    admin_user = is_platform_admin(request.user)

    # Prefetch active Sub-Clans for each Clan
    active_subclans_prefetch = Prefetch(
        'subclan_set',
        queryset=SubClan.objects.filter(is_deleted=False).select_related(
            'parent_road', 'city', 'state'
        ).prefetch_related('managers__user', 'infrastructures').order_by('node_type', 'name'),
        to_attr='active_subclans'
    )

    # Base QuerySets
    clans_qs = Clan.objects.filter(is_deleted=False).select_related(
        'city', 'state', 'geo_political_zone'
    ).prefetch_related('managers__user', active_subclans_prefetch)

    subclans_qs = SubClan.objects.filter(is_deleted=False).select_related(
        'clan', 'city', 'state', 'parent_road'
    ).prefetch_related('managers__user', 'infrastructures')

    # Cached Counts (300s) to eliminate repetitive count round-trips
    total_clans_count = cache.get_or_set('kpi_total_clans', lambda: Clan.objects.filter(is_deleted=False).count(), 300)
    total_subclans_count = cache.get_or_set('kpi_total_subclans', lambda: SubClan.objects.filter(is_deleted=False).count(), 300)
    ROAD_NODE_TYPES = ['MAJOR_ROAD', 'SUB_ROAD', 'STREET', 'CLOSE', 'LINK_ROAD', 'META_ROAD']
    total_roads_count = cache.get_or_set('kpi_total_roads', lambda: SubClan.objects.filter(node_type__in=ROAD_NODE_TYPES, is_deleted=False).count(), 300)
    
    my_clans_count = 0
    if user_profile:
        my_clans_count = cache.get_or_set(
            f'my_clans_count_{user_profile.id}',
            lambda: Clan.objects.filter(
                Q(managers=user_profile) | Q(city__managers=user_profile),
                is_deleted=False
            ).exclude(restricted_users=user_profile).distinct().count(),
            60
        )

    # Filter by view_mode
    if view_mode == 'my' and user_profile:
        clans_qs = clans_qs.filter(
            Q(managers=user_profile) | Q(city__managers=user_profile)
        ).exclude(restricted_users=user_profile).distinct()

    # Filter by State
    selected_state = None
    if state_id:
        selected_state = resolve_state(state_id)
        if selected_state:
            clans_qs = clans_qs.filter(Q(state_id=selected_state.id) | Q(city__state_id=selected_state.id)).distinct()
            subclans_qs = subclans_qs.filter(
                Q(state_id=selected_state.id) | Q(city__state_id=selected_state.id) | Q(clan__state_id=selected_state.id)
            ).distinct()
        else:
            clans_qs = clans_qs.none()
            subclans_qs = subclans_qs.none()

    # Filter by node_type for Sub-Clans
    if node_type_filter:
        subclans_qs = subclans_qs.filter(node_type=node_type_filter)

    # Search Filter
    if query:
        st_match = resolve_state(query)
        if st_match:
            state_search_q = Q(state_id=st_match.id) | Q(city__state_id=st_match.id)
            subclan_state_q = Q(state_id=st_match.id) | Q(city__state_id=st_match.id) | Q(clan__state_id=st_match.id)
        else:
            state_search_q = Q(state__name__iexact=query)
            subclan_state_q = Q(state__name__iexact=query)

        clans_qs = clans_qs.filter(
            Q(name__icontains=query) |
            Q(code__icontains=query) |
            Q(node_id__icontains=query) |
            Q(city__name__icontains=query) |
            Q(geo_political_zone__name__icontains=query) |
            Q(subclan__name__icontains=query) |
            Q(subclan__node_id__icontains=query) |
            Q(managers__user__first_name__icontains=query) |
            Q(managers__user__last_name__icontains=query) |
            Q(managers__user__username__icontains=query) |
            Q(managers__user__email__icontains=query) |
            state_search_q
        ).distinct()

        subclans_qs = subclans_qs.filter(
            Q(name__icontains=query) |
            Q(node_id__icontains=query) |
            Q(clan__name__icontains=query) |
            Q(city__name__icontains=query) |
            Q(managers__user__username__icontains=query) |
            Q(managers__user__email__icontains=query) |
            subclan_state_q
        ).distinct()

    # Filtered counts & smart paginator count bypass
    is_unfiltered = not query and not state_id and view_mode == 'all' and not node_type_filter
    if is_unfiltered:
        filtered_clans_count = total_clans_count
        filtered_subclans_count = total_subclans_count
    else:
        filtered_clans_count = clans_qs.count()
        filtered_subclans_count = subclans_qs.count()

    # Annotate sub-clans count and order in ascending order according to number in state
    clans_qs = clans_qs.annotate(
        subclans_count=Count('subclan', filter=Q(subclan__is_deleted=False))
    )
    if selected_state:
        clans_qs = clans_qs.order_by('id')
    else:
        clans_qs = clans_qs.order_by('state__name', 'id')

    # Pagination
    if view_mode == 'subclans':
        if selected_state:
            subclans_qs = subclans_qs.order_by('id')
        else:
            subclans_qs = subclans_qs.order_by('state__name', 'id')
        paginator = Paginator(subclans_qs, 40)
        if is_unfiltered:
            paginator._count = total_subclans_count
        try:
            page_obj = paginator.page(page)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
        clans_page = None
        subclans_page = page_obj
    else:
        paginator = Paginator(clans_qs, 40)
        if is_unfiltered:
            paginator._count = total_clans_count
        try:
            page_obj = paginator.page(page)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
        clans_page = page_obj
        subclans_page = None

    all_states = cache.get_or_set(
        'all_states_annotated',
        lambda: list(State.objects.filter(is_deleted=False).annotate(
            clans_count=Count('clan_states', filter=Q(clan_states__is_deleted=False))
        ).order_by('name')),
        3600
    )
    all_geo_zones = cache.get_or_set(
        'all_geo_zones_list',
        lambda: list(GeoPoliticalZone.objects.filter(is_deleted=False).order_by('name')),
        3600
    )
    all_clans_dropdown = cache.get_or_set(
        'dropdown_all_clans',
        lambda: list(Clan.objects.filter(is_deleted=False).select_related('city', 'state').only('id', 'name', 'code', 'node_id', 'city_id', 'city__name', 'state_id', 'state__name', 'geo_political_zone_id').order_by('name')),
        3600
    )
    clan_create_form = ClanForm()
    subclan_create_form = None

    context = {
        'clans': clans_page,
        'subclans': subclans_page,
        'page_obj': page_obj,
        'total_clans_count': total_clans_count,
        'total_subclans_count': total_subclans_count,
        'filtered_clans_count': filtered_clans_count,
        'filtered_subclans_count': filtered_subclans_count,
        'selected_state': selected_state,
        'my_clans_count': my_clans_count,
        'query': query,
        'state_id': state_id,
        'view_mode': view_mode,
        'node_type_filter': node_type_filter,
        'all_states': all_states,
        'all_geo_zones': all_geo_zones,
        'all_clans_dropdown': all_clans_dropdown,
        'node_type_choices': NODE_TYPE_CHOICES,
        'road_relation_choices': ROAD_RELATION_CHOICES,
        'road_surface_choices': ROAD_SURFACE_CHOICES,
        'road_condition_choices': ROAD_CONDITION_CHOICES,
        'total_roads_count': total_roads_count,
        'clan_create_form': clan_create_form,
        'subclan_create_form': subclan_create_form,
        'is_admin': admin_user,
    }
    return render(request, 'platform_admin/clans/clan_list.html', context)


@login_required
def subclan_list_view(request):
    """
    Dedicated Directory & listing of all Sub-Clans & Communities
    with search, state filtering, clan filtering, and pagination.
    """
    query = request.GET.get('q', '').strip()
    state_id = request.GET.get('state', '').strip()
    city_id = request.GET.get('city', '').strip() or request.GET.get('lga', '').strip()
    clan_id = request.GET.get('clan', '').strip()
    node_type_filter = request.GET.get('node_type', '').strip()
    page = request.GET.get('page', 1)

    user_profile = getattr(request.user, 'account_profile', None)
    admin_user = is_platform_admin(request.user)

    SUBCLAN_NODE_TYPES = ['SUB_CLAN', 'COMMUNITY']

    # Base query for Sub-Clans & Communities
    subclans_qs = SubClan.objects.filter(
        is_deleted=False
    ).select_related(
        'clan__city', 'clan__state', 'city__state', 'state', 'geo_political_zone'
    ).prefetch_related(
        'managers__user', 'infrastructures', 'connected_streets'
    ).annotate(
        roads_count=Count('connected_streets', filter=Q(connected_streets__is_deleted=False), distinct=True),
        infra_count=Count('infrastructures', filter=Q(infrastructures__is_deleted=False), distinct=True)
    )

    total_subclans_count = cache.get_or_set(
        'kpi_total_pure_subclans',
        lambda: SubClan.objects.filter(node_type__in=SUBCLAN_NODE_TYPES, is_deleted=False).count(),
        300
    )
    subclan_type_count = cache.get_or_set(
        'kpi_subclan_type_count',
        lambda: SubClan.objects.filter(node_type='SUB_CLAN', is_deleted=False).count(),
        300
    )
    community_type_count = cache.get_or_set(
        'kpi_community_type_count',
        lambda: SubClan.objects.filter(node_type='COMMUNITY', is_deleted=False).count(),
        300
    )
    all_nodes_count = cache.get_or_set(
        'kpi_total_all_nodes',
        lambda: SubClan.objects.filter(is_deleted=False).count(),
        300
    )

    # Filter by node_type
    if node_type_filter:
        if node_type_filter in ('SUB_CLAN', 'COMMUNITY', 'STREET', 'MAJOR_ROAD', 'SUB_ROAD', 'CLOSE'):
            subclans_qs = subclans_qs.filter(node_type=node_type_filter)
        elif node_type_filter == 'ALL_NODES':
            pass  # show all territorial nodes
        elif node_type_filter == 'SUB_CLANS_ALL':
            subclans_qs = subclans_qs.filter(node_type__in=SUBCLAN_NODE_TYPES)
    else:
        # Default view: show Sub-Clans & Communities
        # Also include any top-level nodes not explicitly tagged as roads
        subclans_qs = subclans_qs.filter(
            Q(node_type__in=SUBCLAN_NODE_TYPES) | Q(parent_road__isnull=True, node_type__in=['SUB_CLAN', 'COMMUNITY', 'OTHER'])
        )
        if not subclans_qs.exists() and total_subclans_count == 0:
            # Fallback if no records have been tagged yet: show all active records
            subclans_qs = SubClan.objects.filter(is_deleted=False)

    # Filter by state
    selected_state = None
    if state_id:
        selected_state = resolve_state(state_id)
        if selected_state:
            subclans_qs = subclans_qs.filter(
                Q(state_id=selected_state.id) | Q(clan__state_id=selected_state.id) | Q(city__state_id=selected_state.id)
            )
        else:
            subclans_qs = subclans_qs.none()

    # Filter by LGA / City
    selected_city = None
    if city_id:
        try:
            city_id_int = int(city_id)
            selected_city = City.objects.filter(id=city_id_int).first()
            if selected_city and selected_state and selected_city.state_id != selected_state.id:
                selected_city = None
                city_id = None
            if selected_city:
                subclans_qs = subclans_qs.filter(
                    Q(city_id=selected_city.id) | Q(clan__city_id=selected_city.id)
                )
        except (ValueError, TypeError):
            selected_city = City.objects.filter(name__iexact=city_id).first()
            if selected_city and selected_state and selected_city.state_id != selected_state.id:
                selected_city = None
                city_id = None
            if selected_city:
                subclans_qs = subclans_qs.filter(
                    Q(city__name__iexact=city_id) | Q(clan__city__name__iexact=city_id)
                )

    # Filter by clan
    selected_clan = None
    if clan_id:
        try:
            clan_id_int = int(clan_id)
            selected_clan = Clan.objects.filter(id=clan_id_int, is_deleted=False).first()
            if selected_clan and selected_state:
                clan_state_id = getattr(selected_clan, 'state_id', None) or (selected_clan.city.state_id if selected_clan.city else None)
                if clan_state_id != selected_state.id:
                    selected_clan = None
                    clan_id = None
            if selected_clan:
                subclans_qs = subclans_qs.filter(clan_id=clan_id_int)
        except (ValueError, TypeError):
            pass

    # Search query
    if query:
        st_match = resolve_state(query)
        if st_match:
            state_search_q = Q(state_id=st_match.id) | Q(clan__state_id=st_match.id) | Q(city__state_id=st_match.id)
        else:
            state_search_q = Q(state__name__iexact=query)

        subclans_qs = subclans_qs.filter(
            Q(name__icontains=query) |
            Q(node_id__icontains=query) |
            Q(clan__name__icontains=query) |
            Q(city__name__icontains=query) |
            Q(managers__user__first_name__icontains=query) |
            Q(managers__user__last_name__icontains=query) |
            Q(managers__user__username__icontains=query) |
            state_search_q
        ).distinct()

    filtered_subclans_count = subclans_qs.count()
    subclans_qs = subclans_qs.order_by('state__name', 'name')

    # Pagination
    paginator = Paginator(subclans_qs, 25)
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    # Filter dropdown lists
    all_states = cache.get_or_set(
        'all_states_list',
        lambda: list(State.objects.filter(is_deleted=False).order_by('name')),
        3600
    )
    all_clans = cache.get_or_set(
        'dropdown_all_clans',
        lambda: list(Clan.objects.filter(is_deleted=False).select_related('city', 'state').only('id', 'name', 'code', 'node_id', 'city_id', 'city__name', 'state_id', 'state__name', 'geo_political_zone_id').order_by('name')),
        3600
    )
    all_geo_zones = cache.get_or_set(
        'all_geo_zones_list',
        lambda: list(GeoPoliticalZone.objects.filter(is_deleted=False).order_by('name')),
        3600
    )

    # Contextual dropdowns: if state is selected, filter available cities and clans
    if selected_state:
        available_cities = list(City.objects.filter(state=selected_state).order_by('name'))
        available_clans = list(Clan.objects.filter(
            Q(state_id=selected_state.id) | Q(city__state_id=selected_state.id),
            is_deleted=False
        ).select_related('city', 'state').only('id', 'name', 'code', 'node_id', 'city_id', 'city__name', 'state_id', 'state__name').order_by('name'))
    else:
        available_cities = []
        available_clans = all_clans

    context = {
        'page_obj': page_obj,
        'subclans': page_obj.object_list,
        'query': query,
        'state_id': state_id,
        'city_id': city_id,
        'clan_id': clan_id,
        'selected_state': selected_state,
        'selected_city': selected_city,
        'selected_clan': selected_clan,
        'node_type_filter': node_type_filter,
        'total_subclans_count': total_subclans_count,
        'subclan_type_count': subclan_type_count,
        'community_type_count': community_type_count,
        'all_nodes_count': all_nodes_count,
        'filtered_subclans_count': filtered_subclans_count,
        'all_states': all_states,
        'all_clans': all_clans,
        'available_cities': available_cities,
        'available_clans': available_clans,
        'all_geo_zones': all_geo_zones,
        'road_surface_choices': ROAD_SURFACE_CHOICES,
        'road_condition_choices': ROAD_CONDITION_CHOICES,
        'road_relation_choices': ROAD_RELATION_CHOICES,
        'is_admin': admin_user,
    }
    return render(request, 'platform_admin/subclans/subclan_list.html', context)


@login_required
def road_list_view(request, tier=None):
    """
    Dedicated Directory & listing of all Roads (Major Roads, Sub Roads, Streets, Closes)
    with search, tier separation, state & clan filtering, road condition/surface filters,
    and hierarchical connectivity.
    """
    query = request.GET.get('q', '').strip()
    state_id = request.GET.get('state', '').strip()
    clan_id = request.GET.get('clan', '').strip()
    node_type_filter = request.GET.get('node_type', '').strip()
    road_surface_filter = request.GET.get('road_surface', '').strip()
    road_condition_filter = request.GET.get('road_condition', '').strip()
    road_relation_filter = request.GET.get('road_relation', '').strip()
    page = request.GET.get('page', 1)

    # Determine tier from kwargs or GET parameter
    if not tier:
        tier = request.GET.get('tier', '').strip().lower()

    if tier == 'major':
        node_type_filter = 'MAJOR_ROAD'
        tier_title = 'Major Roads (MR)'
        tier_desc = 'Primary arterial trunks connecting clans, cities, and regional transportation corridors.'
    elif tier == 'sub':
        node_type_filter = 'SUB_ROAD'
        tier_title = 'Sub Roads (SR)'
        tier_desc = 'Connector and feeder roads distributing vehicular traffic from Major Roads into local districts and neighborhoods.'
    elif tier == 'street':
        node_type_filter = 'STREET'
        tier_title = 'Streets (STR)'
        tier_desc = 'Urban and neighborhood residential and commercial access ways connected to Sub Roads.'
    elif tier == 'close':
        node_type_filter = 'CLOSE'
        tier_title = 'Closes & Crescents (CLS)'
        tier_desc = 'Terminal residential cul-de-sacs, lanes, and crescents connected to Streets.'
    else:
        tier = 'all'
        if node_type_filter == 'MAJOR_ROAD':
            tier = 'major'
            tier_title = 'Major Roads (MR)'
            tier_desc = 'Primary arterial trunks connecting clans, cities, and regional transportation corridors.'
        elif node_type_filter == 'SUB_ROAD':
            tier = 'sub'
            tier_title = 'Sub Roads (SR)'
            tier_desc = 'Connector and feeder roads distributing vehicular traffic from Major Roads into local districts and neighborhoods.'
        elif node_type_filter == 'STREET':
            tier = 'street'
            tier_title = 'Streets (STR)'
            tier_desc = 'Urban and neighborhood residential and commercial access ways connected to Sub Roads.'
        elif node_type_filter == 'CLOSE':
            tier = 'close'
            tier_title = 'Closes & Crescents (CLS)'
            tier_desc = 'Terminal residential cul-de-sacs, lanes, and crescents connected to Streets.'
        else:
            tier_title = 'All Roads'
            tier_desc = 'Comprehensive directory of all territorial road networks across clans in Nigeria.'

    user_profile = getattr(request.user, 'account_profile', None)
    admin_user = is_platform_admin(request.user)

    ROAD_NODE_TYPES = ['MAJOR_ROAD', 'SUB_ROAD', 'STREET', 'CLOSE', 'LINK_ROAD', 'META_ROAD']

    # Base query for all roads
    roads_qs = SubClan.objects.filter(
        node_type__in=ROAD_NODE_TYPES,
        is_deleted=False
    ).select_related(
        'clan__city', 'clan__state', 'city__state', 'state', 'geo_political_zone', 'parent_road__clan'
    ).prefetch_related(
        'managers__user', 'infrastructures', 'connected_streets'
    ).annotate(
        connected_count=Count('connected_streets', filter=Q(connected_streets__is_deleted=False), distinct=True),
        infra_count=Count('infrastructures', filter=Q(infrastructures__is_deleted=False), distinct=True)
    )

    # KPI counts across all active roads (cached 300s)
    total_roads_count = cache.get_or_set(
        'kpi_total_roads',
        lambda: SubClan.objects.filter(node_type__in=ROAD_NODE_TYPES, is_deleted=False).count(),
        300
    )
    major_roads_count = cache.get_or_set(
        'kpi_major_roads_count',
        lambda: SubClan.objects.filter(node_type__in=['MAJOR_ROAD', 'META_ROAD'], is_deleted=False).count(),
        300
    )
    sub_roads_count = cache.get_or_set(
        'kpi_sub_roads_count',
        lambda: SubClan.objects.filter(node_type__in=['SUB_ROAD', 'LINK_ROAD'], is_deleted=False).count(),
        300
    )
    streets_count = cache.get_or_set(
        'kpi_streets_count',
        lambda: SubClan.objects.filter(node_type='STREET', is_deleted=False).count(),
        300
    )
    closes_count = cache.get_or_set(
        'kpi_closes_count',
        lambda: SubClan.objects.filter(node_type='CLOSE', is_deleted=False).count(),
        300
    )
    total_subclans_count = cache.get_or_set(
        'kpi_total_subclans_count',
        lambda: SubClan.objects.filter(node_type__in=['SUB_CLAN', 'COMMUNITY'], is_deleted=False).count(),
        300
    )

    # Filter by node_type
    if node_type_filter:
        if node_type_filter == 'MAJOR_ROAD':
            roads_qs = roads_qs.filter(node_type__in=['MAJOR_ROAD', 'META_ROAD'])
        elif node_type_filter == 'SUB_ROAD':
            roads_qs = roads_qs.filter(node_type__in=['SUB_ROAD', 'LINK_ROAD'])
        else:
            roads_qs = roads_qs.filter(node_type=node_type_filter)

    # Filter by state
    selected_state = None
    if state_id:
        selected_state = resolve_state(state_id)
        if selected_state:
            roads_qs = roads_qs.filter(
                Q(state_id=selected_state.id) | Q(clan__state_id=selected_state.id) | Q(city__state_id=selected_state.id)
            )
        else:
            roads_qs = roads_qs.none()

    # Filter by clan
    selected_clan = None
    if clan_id:
        try:
            clan_id_int = int(clan_id)
            selected_clan = Clan.objects.filter(id=clan_id_int, is_deleted=False).first()
            if selected_clan and selected_state:
                clan_state_id = getattr(selected_clan, 'state_id', None) or (selected_clan.city.state_id if selected_clan.city else None)
                if clan_state_id != selected_state.id:
                    selected_clan = None
                    clan_id = None
            if selected_clan:
                roads_qs = roads_qs.filter(clan_id=clan_id_int)
        except (ValueError, TypeError):
            pass

    # Filter by surface
    if road_surface_filter:
        roads_qs = roads_qs.filter(road_surface=road_surface_filter)

    # Filter by condition
    if road_condition_filter:
        roads_qs = roads_qs.filter(road_condition=road_condition_filter)

    # Filter by relation / alignment
    if road_relation_filter:
        roads_qs = roads_qs.filter(road_relation=road_relation_filter)

    # Filter by parent subclan
    subclan_id = request.GET.get('subclan')
    selected_subclan = None
    if subclan_id:
        try:
            subclan_id_int = int(subclan_id)
            selected_subclan = SubClan.objects.filter(id=subclan_id_int, is_deleted=False).first()
            if selected_subclan:
                if selected_clan and selected_subclan.clan_id != selected_clan.id:
                    selected_subclan = None
                    subclan_id = None
                elif selected_state:
                    sc_state_id = selected_subclan.state_id or (selected_subclan.clan.state_id if selected_subclan.clan else None) or (selected_subclan.city.state_id if selected_subclan.city else None)
                    if sc_state_id and sc_state_id != selected_state.id:
                        selected_subclan = None
                        subclan_id = None

            if selected_subclan:
                roads_qs = roads_qs.filter(
                    Q(parent_road_id=subclan_id_int) |
                    Q(parent_road__parent_road_id=subclan_id_int) |
                    Q(parent_road__parent_road__parent_road_id=subclan_id_int) |
                    (Q(node_id__startswith=f"{selected_subclan.node_id}/") if selected_subclan.node_id else Q(parent_road_id=subclan_id_int))
                )
        except (ValueError, TypeError):
            pass

    # Search query
    if query:
        st_match = resolve_state(query)
        if st_match:
            state_search_q = Q(state_id=st_match.id) | Q(clan__state_id=st_match.id) | Q(city__state_id=st_match.id)
        else:
            state_search_q = Q(state__name__iexact=query)

        roads_qs = roads_qs.filter(
            Q(name__icontains=query) |
            Q(node_id__icontains=query) |
            Q(clan__name__icontains=query) |
            Q(city__name__icontains=query) |
            Q(parent_road__name__icontains=query) |
            state_search_q
        )

    roads_qs = roads_qs.order_by('node_type', 'name')

    # Pagination
    paginator = Paginator(roads_qs, 25)
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    # Filter dropdown lists
    all_states = cache.get_or_set(
        'all_states_list',
        lambda: list(State.objects.filter(is_deleted=False).order_by('name')),
        3600
    )
    all_clans = cache.get_or_set(
        'dropdown_all_clans',
        lambda: list(Clan.objects.filter(is_deleted=False).select_related('city', 'state').only('id', 'name', 'code', 'node_id', 'city_id', 'city__name', 'state_id', 'state__name', 'geo_political_zone_id').order_by('name')),
        3600
    )
    all_geo_zones = cache.get_or_set(
        'all_geo_zones_list',
        lambda: list(GeoPoliticalZone.objects.filter(is_deleted=False).order_by('name')),
        3600
    )
    # Available clans for dropdown (with respect to selected state)
    if selected_state:
        available_clans = list(Clan.objects.filter(
            Q(state_id=selected_state.id) | Q(city__state_id=selected_state.id),
            is_deleted=False
        ).select_related('city', 'state').only('id', 'name', 'code', 'node_id', 'city_id', 'city__name', 'state_id', 'state__name').order_by('name'))
    else:
        available_clans = all_clans

    # Available sub-clans for dropdown (with respect to selected parent clan)
    if selected_clan:
        available_subclans = list(SubClan.objects.filter(
            clan_id=selected_clan.id,
            node_type__in=['SUB_CLAN', 'COMMUNITY'],
            is_deleted=False
        ).select_related('clan').only('id', 'name', 'node_id', 'node_type', 'clan_id', 'clan__name').order_by('name'))
        all_subclans_for_parent = list(SubClan.objects.filter(
            clan_id=selected_clan.id,
            is_deleted=False
        ).select_related('clan').only('id', 'name', 'node_id', 'node_type', 'clan_id').order_by('node_type', 'name'))
    elif selected_state:
        available_subclans = list(SubClan.objects.filter(
            Q(state_id=selected_state.id) | Q(clan__state_id=selected_state.id) | Q(city__state_id=selected_state.id),
            node_type__in=['SUB_CLAN', 'COMMUNITY'],
            is_deleted=False
        ).select_related('clan').only('id', 'name', 'node_id', 'node_type', 'clan_id', 'clan__name').order_by('clan__name', 'name')[:300])
        all_subclans_for_parent = list(SubClan.objects.filter(
            Q(state_id=selected_state.id) | Q(clan__state_id=selected_state.id) | Q(city__state_id=selected_state.id),
            node_type__in=['MAJOR_ROAD', 'SUB_ROAD', 'STREET', 'SUB_CLAN', 'COMMUNITY'],
            is_deleted=False
        ).select_related('clan').only('id', 'name', 'node_id', 'node_type', 'clan_id').order_by('node_type', 'name')[:250])
    else:
        available_subclans = []
        all_subclans_for_parent = []

    raw_subclans_json = json.dumps([
        {
            'id': sc.id,
            'name': sc.name,
            'node_id': sc.node_id or '',
            'node_type': sc.node_type or '',
            'clan_id': sc.clan_id
        }
        for sc in all_subclans_for_parent
    ])

    road_node_choices = (
        ('MAJOR_ROAD', 'Major Road (MR)'),
        ('SUB_ROAD', 'Sub Road (SR)'),
        ('STREET', 'Street (STR)'),
        ('CLOSE', 'Close / Crescent (CLS)'),
    )

    context = {
        'page_obj': page_obj,
        'roads': page_obj.object_list,
        'query': query,
        'state_id': state_id,
        'clan_id': clan_id,
        'subclan_id': subclan_id,
        'selected_state': selected_state,
        'selected_clan': selected_clan,
        'selected_subclan': selected_subclan,
        'tier': tier,
        'tier_title': tier_title,
        'tier_desc': tier_desc,
        'node_type_filter': node_type_filter,
        'road_surface_filter': road_surface_filter,
        'road_condition_filter': road_condition_filter,
        'road_relation_filter': road_relation_filter,
        'total_roads_count': total_roads_count,
        'major_roads_count': major_roads_count,
        'sub_roads_count': sub_roads_count,
        'streets_count': streets_count,
        'closes_count': closes_count,
        'total_subclans_count': total_subclans_count,
        'filtered_roads_count': paginator.count,
        'all_states': all_states,
        'all_clans': all_clans,
        'available_clans': available_clans,
        'available_subclans': available_subclans,
        'all_subclans_for_parent': all_subclans_for_parent,
        'raw_subclans_json': raw_subclans_json,
        'all_geo_zones': all_geo_zones,
        'road_node_choices': road_node_choices,
        'node_type_choices': NODE_TYPE_CHOICES,
        'road_surface_choices': ROAD_SURFACE_CHOICES,
        'road_condition_choices': ROAD_CONDITION_CHOICES,
        'road_relation_choices': ROAD_RELATION_CHOICES,
        'is_admin': admin_user,
    }
    return render(request, 'platform_admin/roads/road_list.html', context)


@login_required
def clan_detail_view(request, pk):
    """
    Detailed management page for a single Clan:
    - Overview details
    - Edit Clan form / modal
    - Sub-Clans list with 'Add Sub-Clan', 'Edit', and 'Delete'
    - Delegated Managers / Access delegation with 'Grant Access' and 'Revoke'
    - Associated Data (Historical, Market Sector, Geo-Physical)
    """
    clan = get_object_or_404(
        Clan.objects.select_related('city', 'state', 'geo_political_zone', 'country'),
        id=pk,
        is_deleted=False
    )

    can_manage = can_user_manage_clan(request.user, clan)
    is_admin = is_platform_admin(request.user)

    # Sub-clans under this clan
    subclans = list(clan.subclan_set.filter(is_deleted=False).select_related(
        'city', 'state', 'parent_road'
    ).prefetch_related('managers__user', 'infrastructures').order_by('name'))
    subclans_count = len(subclans)

    # Territorial infrastructure records under this clan
    infrastructures = list(clan.clan_infrastructures.filter(is_deleted=False).select_related(
        'subclan'
    ).order_by('-date_created'))
    infrastructure_count = len(infrastructures)
    drainage_count = sum(1 for inf in infrastructures if inf.infrastructure_type == 'DRAINAGE')
    street_light_count = sum(1 for inf in infrastructures if inf.infrastructure_type == 'STREET_LIGHT')
    other_infra_count = max(0, infrastructure_count - (drainage_count + street_light_count))

    # Data records under this clan
    historical_records = list(Historical.objects.filter(clan=clan, is_deleted=False).select_related('category').order_by('-date_created')[:15])
    historical_count = Historical.objects.filter(clan=clan, is_deleted=False).count()

    market_records = list(MarketSector.objects.filter(clan=clan, is_deleted=False).select_related('category', 'sub_category').order_by('-date_created')[:15])
    market_count = MarketSector.objects.filter(clan=clan, is_deleted=False).count()

    geo_records = list(GeoPhysicalData.objects.filter(clan=clan, is_deleted=False).select_related('category').order_by('-date_created')[:15])
    geo_count = GeoPhysicalData.objects.filter(clan=clan, is_deleted=False).count()

    # Managers with access
    assigned_managers = clan.managers.all().select_related('user').order_by('user__first_name')
    city_managers = clan.city.managers.all().select_related('user') if clan.city else []

    # Active accounts for grant modal
    users = Account.objects.filter(is_active=True).select_related('account_profile').order_by('first_name', 'username')

    # Forms
    clan_edit_form = ClanForm(instance=clan)
    subclan_create_form = SubClanForm(initial={
        'clan': clan,
        'state': clan.state,
        'city': clan.city
    })
    infrastructure_create_form = TerritorialInfrastructureForm(initial={
        'clan': clan
    })

    context = {
        'clan': clan,
        'can_manage': can_manage,
        'is_admin': is_admin,
        'subclans': subclans,
        'subclans_count': subclans_count,
        'infrastructures': infrastructures,
        'infrastructure_count': infrastructure_count,
        'drainage_count': drainage_count,
        'street_light_count': street_light_count,
        'other_infra_count': other_infra_count,
        'historical_records': historical_records,
        'historical_count': historical_count,
        'market_records': market_records,
        'market_count': market_count,
        'geo_records': geo_records,
        'geo_count': geo_count,
        'assigned_managers': assigned_managers,
        'city_managers': city_managers,
        'users': users,
        'clan_edit_form': clan_edit_form,
        'subclan_create_form': subclan_create_form,
        'infrastructure_create_form': infrastructure_create_form,
        'node_type_choices': NODE_TYPE_CHOICES,
        'road_relation_choices': ROAD_RELATION_CHOICES,
        'road_surface_choices': ROAD_SURFACE_CHOICES,
        'road_condition_choices': ROAD_CONDITION_CHOICES,
        'infrastructure_type_choices': INFRASTRUCTURE_TYPE_CHOICES,
        'infrastructure_status_choices': INFRASTRUCTURE_STATUS_CHOICES,
        'side_of_road_choices': SIDE_OF_ROAD_CHOICES,
    }
    return render(request, 'platform_admin/clans/clan_detail.html', context)


@login_required
def clan_create_view(request):
    """
    Create a new Clan with PRD Node ID convention.
    """
    next_url = request.POST.get('next', '').strip()
    if request.method == "POST":
        form = ClanForm(request.POST)
        if form.is_valid():
            clan = form.save()
            # If user is not admin, automatically assign them as a manager so they can manage it
            if hasattr(request.user, 'account_profile'):
                clan.managers.add(request.user.account_profile)
                if not request.user.is_data_agent:
                    request.user.is_data_agent = True
                    request.user.save(update_fields=['is_data_agent'])

            invalidate_clan_caches()
            messages.success(request, f"Clan '{clan.name}' [{clan.display_node_id}] created successfully! You can now input data and add sub-clans.")
            if next_url:
                return redirect(next_url)
            return redirect('platform_admin:clan-detail', pk=clan.pk)
        else:
            errors = " ".join([f"{f}: {', '.join(e)}" for f, e in form.errors.items()])
            messages.error(request, f"Failed to create clan. {errors}")
            if next_url:
                return redirect(next_url)
            return redirect('platform_admin:clan-list')

    return redirect(next_url or 'platform_admin:clan-list')


@login_required
def clan_edit_view(request, pk):
    """
    Modify an existing Clan.
    """
    clan = get_object_or_404(Clan, id=pk, is_deleted=False)

    if not can_user_manage_clan(request.user, clan):
        messages.error(request, f"You do not have permission to modify '{clan.name}' Clan.")
        return redirect('platform_admin:clan-detail', pk=clan.pk)

    if request.method == "POST":
        form = ClanForm(request.POST, instance=clan)
        if form.is_valid():
            form.save()
            invalidate_clan_caches()
            messages.success(request, f"Clan '{clan.name}' updated successfully.")
            return redirect('platform_admin:clan-detail', pk=clan.pk)
        else:
            errors = " ".join([f"{f}: {', '.join(e)}" for f, e in form.errors.items()])
            messages.error(request, f"Error updating clan. {errors}")
            return redirect('platform_admin:clan-detail', pk=clan.pk)

    return redirect('platform_admin:clan-detail', pk=clan.pk)


@login_required
def clan_delete_view(request, pk):
    """
    Soft delete a Clan.
    """
    clan = get_object_or_404(Clan, id=pk, is_deleted=False)

    if not (is_platform_admin(request.user) or can_user_manage_clan(request.user, clan)):
        messages.error(request, f"You do not have permission to delete '{clan.name}' Clan.")
        return redirect('platform_admin:clan-detail', pk=clan.pk)

    if request.method == "POST":
        clan.is_deleted = True
        clan.save(update_fields=['is_deleted'])
        invalidate_clan_caches()
        messages.info(request, f"Clan '{clan.name}' has been archived/deleted.")
        next_url = request.POST.get('next') or request.META.get('HTTP_REFERER')
        clan_detail_url = reverse('platform_admin:clan-detail', kwargs={'pk': clan.pk})
        if next_url and clan_detail_url not in next_url:
            return redirect(next_url)
        return redirect('platform_admin:clan-list')

    return redirect('platform_admin:clan-detail', pk=clan.pk)


@login_required
def subclan_create_for_clan_view(request, clan_id):
    """
    Add a new Sub-Clan / Territorial Node directly under a parent Clan.
    Follows PRD Node ID convention: [Territory]-[Node Type]-[Sequential Number]
    Supports parent road connectivity, road surface, and road condition.
    """
    clan = get_object_or_404(Clan, id=clan_id, is_deleted=False)
    next_url = request.POST.get('next', '').strip()

    if not can_user_manage_clan(request.user, clan):
        messages.error(request, f"You do not have permission to add sub-nodes to '{clan.name}' Clan.")
        return redirect(next_url or reverse('platform_admin:clan-detail', kwargs={'pk': clan.pk}))

    if request.method == "POST":
        name = request.POST.get('name', '').strip()
        node_type = request.POST.get('node_type', 'MAJOR_ROAD').strip() or 'MAJOR_ROAD'
        road_relation = request.POST.get('road_relation', 'CONTAINED_CLAN').strip() or 'CONTAINED_CLAN'
        node_id = request.POST.get('node_id', '').strip()
        parent_road_id = request.POST.get('parent_road')
        road_surface = request.POST.get('road_surface', 'ASPHALT').strip() or 'ASPHALT'
        road_condition = request.POST.get('road_condition', 'GOOD').strip() or 'GOOD'

        if not name:
            messages.error(request, "Sub-clan / Node name is required.")
            return redirect(next_url or reverse('platform_admin:clan-detail', kwargs={'pk': clan.pk}))

        city_id = request.POST.get('city') or (clan.city.id if clan.city else None)
        state_id = request.POST.get('state') or (clan.state.id if clan.state else None)

        city = City.objects.filter(id=city_id).first() if city_id else clan.city
        state = State.objects.filter(id=state_id).first() if state_id else (city.state if city else clan.state)
        geo_zone = (state.geo_political_zone if state else clan.geo_political_zone)

        # Tie Clan to LGA (city) if clan lacked an LGA
        if city and not clan.city:
            clan.city = city
            if not clan.state and state:
                clan.state = state
            if not clan.geo_political_zone and geo_zone:
                clan.geo_political_zone = geo_zone
            clan.save(update_fields=['city', 'state', 'geo_political_zone'])

        parent_road = SubClan.objects.filter(id=parent_road_id, is_deleted=False).first() if parent_road_id else None

        # Enforce territorial architecture hierarchy:
        # Sub-Clans -> Clan; Major Roads -> Sub-Clan or Clan (Contained or Passing); Sub Roads -> Major Road; Streets -> Sub Road; Closes -> Street
        if node_type in ('SUB_CLAN', 'COMMUNITY'):
            parent_road = None
        elif node_type in ('MAJOR_ROAD', 'META_ROAD'):
            if parent_road and parent_road.node_type in ('SUB_CLAN', 'COMMUNITY'):
                if road_relation in ('CONTAINED_CLAN', 'PASSING_CLAN'):
                    road_relation = 'CONTAINED_SUBCLAN'
            elif road_relation in ('CONTAINED_CLAN', 'PASSING_CLAN'):
                parent_road = None
            elif road_relation in ('CONTAINED_SUBCLAN', 'PASSING_SUBCLAN'):
                if parent_road and parent_road.node_type not in ('SUB_CLAN', 'COMMUNITY'):
                    messages.error(request, "Major Roads aligned with a Sub-Clan must have a Sub-Clan / Community as parent.")
                    return redirect(next_url or reverse('platform_admin:clan-detail', kwargs={'pk': clan.pk}))
        elif node_type in ('SUB_ROAD', 'LINK_ROAD'):
            if not parent_road:
                messages.error(request, "Sub Roads must belong to a Major Road.")
                return redirect(next_url or reverse('platform_admin:clan-detail', kwargs={'pk': clan.pk}))
            if parent_road.node_type not in ('MAJOR_ROAD', 'META_ROAD'):
                messages.error(request, f"Sub Roads must belong to a Major Road (selected '{parent_road.name}' is {parent_road.get_node_type_display()}).")
                return redirect(next_url or reverse('platform_admin:clan-detail', kwargs={'pk': clan.pk}))
        elif node_type == 'STREET':
            if not parent_road:
                messages.error(request, "Streets must belong to a Sub Road.")
                return redirect(next_url or reverse('platform_admin:clan-detail', kwargs={'pk': clan.pk}))
            if parent_road.node_type not in ('SUB_ROAD', 'LINK_ROAD'):
                messages.error(request, f"Streets must belong to a Sub Road (selected '{parent_road.name}' is {parent_road.get_node_type_display()}).")
                return redirect(next_url or reverse('platform_admin:clan-detail', kwargs={'pk': clan.pk}))
        elif node_type == 'CLOSE':
            if not parent_road:
                messages.error(request, "Closes must belong to a Street.")
                return redirect(next_url or reverse('platform_admin:clan-detail', kwargs={'pk': clan.pk}))
            if parent_road.node_type != 'STREET':
                messages.error(request, f"Closes must belong to a Street (selected '{parent_road.name}' is {parent_road.get_node_type_display()}).")
                return redirect(next_url or reverse('platform_admin:clan-detail', kwargs={'pk': clan.pk}))

        subclan = SubClan(
            name=name,
            clan=clan,
            node_type=node_type,
            road_relation=road_relation,
            parent_road=parent_road,
            road_surface=road_surface,
            road_condition=road_condition,
            city=city,
            state=state,
            geo_political_zone=geo_zone,
            country=clan.country or Country.my_objects.first() or Country.objects.first()
        )
        if node_id:
            subclan.node_id = node_id
        else:
            subclan.node_id = subclan.generate_next_node_id()
        subclan.save()

        # Inherit current user as manager
        if hasattr(request.user, 'account_profile'):
            subclan.managers.add(request.user.account_profile)

        invalidate_clan_caches()
        messages.success(request, f"Territorial Node '{subclan.name}' [{subclan.display_node_id}] created successfully under '{clan.name}'.")
        return redirect(next_url or reverse('platform_admin:clan-detail', kwargs={'pk': clan.pk}))

    return redirect(next_url or reverse('platform_admin:clan-detail', kwargs={'pk': clan.pk}))


@login_required
def subclan_create_general_view(request):
    """
    Create a new sub-clan / territorial node when clan is selected via form dropdown.
    Enables creating sub-clans directly from the dashboard and global action hubs.
    """
    next_url = request.POST.get('next', '').strip()
    if request.method == "POST":
        clan_id = request.POST.get('clan')
        if not clan_id:
            messages.error(request, "Please select a parent Clan for this territorial node.")
            return redirect(next_url or 'platform_admin:dashboard')

        clan = get_object_or_404(Clan, id=clan_id, is_deleted=False)
        if not can_user_manage_clan(request.user, clan):
            messages.error(request, f"You do not have permission to add sub-nodes to '{clan.name}'.")
            return redirect(next_url or 'platform_admin:dashboard')

        name = request.POST.get('name', '').strip()
        node_type = request.POST.get('node_type', 'MAJOR_ROAD').strip() or 'MAJOR_ROAD'
        road_relation = request.POST.get('road_relation', 'CONTAINED_CLAN').strip() or 'CONTAINED_CLAN'
        node_id = request.POST.get('node_id', '').strip()
        parent_road_id = request.POST.get('parent_road')
        road_surface = request.POST.get('road_surface', 'ASPHALT').strip() or 'ASPHALT'
        road_condition = request.POST.get('road_condition', 'GOOD').strip() or 'GOOD'

        if not name:
            messages.error(request, "Node name is required.")
            return redirect(next_url or 'platform_admin:dashboard')

        city_id = request.POST.get('city') or (clan.city.id if clan.city else None)
        state_id = request.POST.get('state') or (clan.state.id if clan.state else None)
        city = City.objects.filter(id=city_id).first() if city_id else clan.city
        state = State.objects.filter(id=state_id).first() if state_id else (city.state if city else clan.state)
        geo_zone_id = request.POST.get('geo_political_zone')
        geo_zone = GeoPoliticalZone.objects.filter(id=geo_zone_id).first() if geo_zone_id else (
            (state.geo_political_zone if state else None) or (city.state.geo_political_zone if city and city.state else None) or clan.geo_political_zone
        )

        # Tie Clan to LGA (city) if clan lacked an LGA
        if city and not clan.city:
            clan.city = city
            if not clan.state and state:
                clan.state = state
            if not clan.geo_political_zone and geo_zone:
                clan.geo_political_zone = geo_zone
            clan.save(update_fields=['city', 'state', 'geo_political_zone'])

        parent_road = SubClan.objects.filter(id=parent_road_id, is_deleted=False).first() if parent_road_id else None

        # Enforce territorial architecture hierarchy:
        # Sub-Clans -> Clan; Major Roads -> Sub-Clan or Clan (Contained or Passing); Sub Roads -> Major Road; Streets -> Sub Road; Closes -> Street
        if node_type in ('SUB_CLAN', 'COMMUNITY'):
            parent_road = None
        elif node_type in ('MAJOR_ROAD', 'META_ROAD'):
            if parent_road and parent_road.node_type in ('SUB_CLAN', 'COMMUNITY'):
                if road_relation in ('CONTAINED_CLAN', 'PASSING_CLAN'):
                    road_relation = 'CONTAINED_SUBCLAN'
            elif road_relation in ('CONTAINED_CLAN', 'PASSING_CLAN'):
                parent_road = None
            elif road_relation in ('CONTAINED_SUBCLAN', 'PASSING_SUBCLAN'):
                if parent_road and parent_road.node_type not in ('SUB_CLAN', 'COMMUNITY'):
                    messages.error(request, "Major Roads aligned with a Sub-Clan must have a Sub-Clan / Community as parent.")
                    return redirect(next_url or 'platform_admin:dashboard')
        elif node_type in ('SUB_ROAD', 'LINK_ROAD'):
            if not parent_road:
                messages.error(request, "Sub Roads must belong to a Major Road.")
                return redirect(next_url or 'platform_admin:dashboard')
            if parent_road.node_type not in ('MAJOR_ROAD', 'META_ROAD'):
                messages.error(request, f"Sub Roads must belong to a Major Road (selected '{parent_road.name}' is {parent_road.get_node_type_display()}).")
                return redirect(next_url or 'platform_admin:dashboard')
        elif node_type == 'STREET':
            if not parent_road:
                messages.error(request, "Streets must belong to a Sub Road.")
                return redirect(next_url or 'platform_admin:dashboard')
            if parent_road.node_type not in ('SUB_ROAD', 'LINK_ROAD'):
                messages.error(request, f"Streets must belong to a Sub Road (selected '{parent_road.name}' is {parent_road.get_node_type_display()}).")
                return redirect(next_url or 'platform_admin:dashboard')
        elif node_type == 'CLOSE':
            if not parent_road:
                messages.error(request, "Closes must belong to a Street.")
                return redirect(next_url or 'platform_admin:dashboard')
            if parent_road.node_type != 'STREET':
                messages.error(request, f"Closes must belong to a Street (selected '{parent_road.name}' is {parent_road.get_node_type_display()}).")
                return redirect(next_url or 'platform_admin:dashboard')

        subclan = SubClan(
            name=name,
            clan=clan,
            node_type=node_type,
            road_relation=road_relation,
            parent_road=parent_road,
            road_surface=road_surface,
            road_condition=road_condition,
            city=city,
            state=state,
            geo_political_zone=geo_zone,
            country=clan.country or Country.my_objects.first() or Country.objects.first()
        )
        if node_id:
            subclan.node_id = node_id
        else:
            subclan.node_id = subclan.generate_next_node_id()
        subclan.save()

        if hasattr(request.user, 'account_profile'):
            subclan.managers.add(request.user.account_profile)

        invalidate_clan_caches()
        messages.success(request, f"Territorial Node '{subclan.name}' [{subclan.display_node_id}] created successfully under '{clan.name}'.")
        return redirect(next_url or reverse('platform_admin:clan-detail', kwargs={'pk': clan.pk}))

    return redirect(next_url or 'platform_admin:dashboard')


@login_required
def subclan_edit_view(request, pk):
    """
    Edit a Sub-Clan / Territorial Node.
    """
    subclan = get_object_or_404(SubClan, id=pk, is_deleted=False)

    if not can_user_manage_subclan(request.user, subclan):
        messages.error(request, f"You do not have permission to modify '{subclan.name}' Sub-Clan.")
        next_url = request.POST.get('next') or request.META.get('HTTP_REFERER')
        return redirect(next_url or 'platform_admin:clan-list')

    if request.method == "POST":
        name = request.POST.get('name', '').strip()
        if not name:
            messages.error(request, "Sub-clan name cannot be empty.")
        else:
            subclan.name = name

            node_type = request.POST.get('node_type')
            if node_type:
                subclan.node_type = node_type

            road_relation = request.POST.get('road_relation')
            if road_relation:
                subclan.road_relation = road_relation

            parent_road_id = request.POST.get('parent_road')
            if parent_road_id is not None:
                if parent_road_id == '' or parent_road_id == '0':
                    subclan.parent_road = None
                else:
                    subclan.parent_road = SubClan.objects.filter(id=parent_road_id, is_deleted=False).first()

            road_surface = request.POST.get('road_surface')
            if road_surface:
                subclan.road_surface = road_surface

            road_condition = request.POST.get('road_condition')
            if road_condition:
                subclan.road_condition = road_condition

            city_id = request.POST.get('city')
            state_id = request.POST.get('state')

            if city_id:
                subclan.city = City.objects.filter(id=city_id).first()
            if state_id:
                subclan.state = State.objects.filter(id=state_id).first()

            subclan.save()
            invalidate_clan_caches()
            messages.success(request, f"Territorial Node '{subclan.name}' updated successfully.")

    next_url = request.POST.get('next') or (
        reverse('platform_admin:clan-detail', kwargs={'pk': subclan.clan.pk}) if subclan.clan else None
    )
    return redirect(next_url or 'platform_admin:clan-list')


@login_required
def subclan_delete_view(request, pk):
    """
    Soft delete a Sub-Clan.
    """
    subclan = get_object_or_404(SubClan, id=pk, is_deleted=False)

    if not can_user_manage_subclan(request.user, subclan):
        messages.error(request, f"You do not have permission to delete '{subclan.name}' Sub-Clan.")
        next_url = request.POST.get('next') or request.META.get('HTTP_REFERER')
        return redirect(next_url or 'platform_admin:clan-list')

    if request.method == "POST":
        subclan.is_deleted = True
        subclan.save(update_fields=['is_deleted'])
        invalidate_clan_caches()
        node_label = subclan.get_node_type_display() if hasattr(subclan, 'get_node_type_display') else "Territorial Node"
        messages.info(request, f"{node_label} '{subclan.name}' has been archived.")

    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or (
        reverse('platform_admin:clan-detail', kwargs={'pk': subclan.clan.pk}) if subclan.clan else None
    )
    return redirect(next_url or 'platform_admin:clan-list')


@login_required
def infrastructure_create_for_clan_view(request, clan_id):
    """
    Create a new TerritorialInfrastructure (Drainage, Street Light, etc.) for a Clan/SubClan.
    """
    clan = get_object_or_404(Clan, id=clan_id, is_deleted=False)
    next_url = request.POST.get('next', '').strip()

    if not can_user_manage_clan(request.user, clan):
        messages.error(request, f"You do not have permission to add infrastructure to '{clan.name}' Clan.")
        return redirect(next_url or reverse('platform_admin:clan-detail', kwargs={'pk': clan.pk}))

    if request.method == "POST":
        name = request.POST.get('name', '').strip()
        infrastructure_type = request.POST.get('infrastructure_type', 'DRAINAGE').strip()
        subclan_id = request.POST.get('subclan')
        status = request.POST.get('status', 'OPERATIONAL').strip()
        side_of_road = request.POST.get('side_of_road', 'BOTH').strip()
        quantity_str = request.POST.get('quantity', '1')
        coverage_str = request.POST.get('coverage_length_meters', '').strip()
        installed_by = request.POST.get('installed_by', '').strip()
        year_str = request.POST.get('year_installed', '').strip()
        gps_coordinates = request.POST.get('gps_coordinates', '').strip()
        description = request.POST.get('description', '').strip()

        if not name:
            messages.error(request, "Infrastructure asset name is required.")
            return redirect(next_url or reverse('platform_admin:clan-detail', kwargs={'pk': clan.pk}))

        try:
            quantity = int(quantity_str) if quantity_str else 1
        except ValueError:
            quantity = 1

        coverage_length = None
        if coverage_str:
            try:
                coverage_length = float(coverage_str)
            except ValueError:
                coverage_length = None

        year_installed = None
        if year_str:
            try:
                year_installed = int(year_str)
            except ValueError:
                year_installed = None

        subclan = SubClan.objects.filter(id=subclan_id, clan=clan, is_deleted=False).first() if subclan_id else None

        infra = TerritorialInfrastructure.objects.create(
            clan=clan,
            subclan=subclan,
            name=name,
            infrastructure_type=infrastructure_type,
            status=status,
            side_of_road=side_of_road,
            quantity=quantity,
            coverage_length_meters=coverage_length,
            installed_by=installed_by,
            year_installed=year_installed,
            gps_coordinates=gps_coordinates,
            description=description,
        )

        messages.success(request, f"Territorial infrastructure '{infra.name}' [{infra.get_infrastructure_type_display()}] created successfully.")
        return redirect(next_url or reverse('platform_admin:clan-detail', kwargs={'pk': clan.pk}))

    return redirect(next_url or reverse('platform_admin:clan-detail', kwargs={'pk': clan.pk}))


@login_required
def infrastructure_edit_view(request, pk):
    """
    Edit a TerritorialInfrastructure record.
    """
    infra = get_object_or_404(TerritorialInfrastructure, id=pk, is_deleted=False)
    clan = infra.clan
    next_url = request.POST.get('next', '').strip()

    if not can_user_manage_clan(request.user, clan):
        messages.error(request, "You do not have permission to modify this infrastructure record.")
        return redirect(next_url or reverse('platform_admin:clan-detail', kwargs={'pk': clan.pk}))

    if request.method == "POST":
        name = request.POST.get('name', '').strip()
        if not name:
            messages.error(request, "Infrastructure name cannot be empty.")
            return redirect(next_url or reverse('platform_admin:clan-detail', kwargs={'pk': clan.pk}))

        infra.name = name
        infra_type = request.POST.get('infrastructure_type')
        if infra_type:
            infra.infrastructure_type = infra_type

        subclan_id = request.POST.get('subclan')
        if subclan_id is not None:
            if subclan_id == '' or subclan_id == '0':
                infra.subclan = None
            else:
                infra.subclan = SubClan.objects.filter(id=subclan_id, clan=clan, is_deleted=False).first()

        status = request.POST.get('status')
        if status:
            infra.status = status

        side_of_road = request.POST.get('side_of_road')
        if side_of_road:
            infra.side_of_road = side_of_road

        quantity_str = request.POST.get('quantity')
        if quantity_str:
            try:
                infra.quantity = int(quantity_str)
            except ValueError:
                pass

        coverage_str = request.POST.get('coverage_length_meters', '').strip()
        if coverage_str:
            try:
                infra.coverage_length_meters = float(coverage_str)
            except ValueError:
                infra.coverage_length_meters = None
        elif coverage_str == '':
            infra.coverage_length_meters = None

        infra.installed_by = request.POST.get('installed_by', '').strip()
        year_str = request.POST.get('year_installed', '').strip()
        if year_str:
            try:
                infra.year_installed = int(year_str)
            except ValueError:
                infra.year_installed = None
        elif year_str == '':
            infra.year_installed = None

        infra.gps_coordinates = request.POST.get('gps_coordinates', '').strip()
        infra.description = request.POST.get('description', '').strip()
        infra.save()

        messages.success(request, f"Territorial infrastructure '{infra.name}' updated successfully.")

    return redirect(next_url or reverse('platform_admin:clan-detail', kwargs={'pk': clan.pk}))


@login_required
def infrastructure_delete_view(request, pk):
    """
    Soft delete a TerritorialInfrastructure record.
    """
    infra = get_object_or_404(TerritorialInfrastructure, id=pk, is_deleted=False)
    clan = infra.clan
    next_url = request.POST.get('next', '').strip()

    if not can_user_manage_clan(request.user, clan):
        messages.error(request, "You do not have permission to delete this infrastructure record.")
        return redirect(next_url or reverse('platform_admin:clan-detail', kwargs={'pk': clan.pk}))

    if request.method == "POST":
        infra.is_deleted = True
        infra.save(update_fields=['is_deleted'])
        messages.info(request, f"Infrastructure asset '{infra.name}' has been archived.")

    return redirect(next_url or reverse('platform_admin:clan-detail', kwargs={'pk': clan.pk}))


@login_required
def subclan_delete_view(request, pk):
    """
    Soft delete a Sub-Clan.
    """
    subclan = get_object_or_404(SubClan, id=pk, is_deleted=False)

    if not can_user_manage_subclan(request.user, subclan):
        messages.error(request, f"You do not have permission to delete '{subclan.name}' Sub-Clan.")
        next_url = request.POST.get('next') or request.META.get('HTTP_REFERER')
        return redirect(next_url or 'platform_admin:clan-list')

    if request.method == "POST":
        subclan.is_deleted = True
        subclan.save(update_fields=['is_deleted'])
        messages.info(request, f"Sub-Clan '{subclan.name}' has been archived/deleted.")

    next_url = request.POST.get('next') or (
        reverse('platform_admin:clan-detail', kwargs={'pk': subclan.clan.pk}) if subclan.clan else None
    )
    return redirect(next_url or 'platform_admin:clan-list')


@login_required
def clan_grant_access_view(request, pk):
    """
    Grant access to a user to manage this clan, add sub-clans, and submit/modify data.
    """
    clan = get_object_or_404(Clan, id=pk, is_deleted=False)

    if not can_user_manage_clan(request.user, clan):
        messages.error(request, "You do not have permission to grant access for this clan.")
        return redirect('platform_admin:clan-detail', pk=clan.pk)

    next_url = request.POST.get('next', '').strip()
    if request.method == "POST":
        profile_id = request.POST.get("profile_id")
        if not profile_id:
            messages.error(request, "Please select a user to grant access.")
            return redirect(next_url or reverse('platform_admin:clan-detail', kwargs={'pk': clan.pk}))

        profile = Profile.objects.filter(id=profile_id).first()
        if not profile:
            profile = Profile.objects.filter(user_id=profile_id).first()
        if not profile:
            u_obj = Account.objects.filter(id=profile_id).first()
            if u_obj:
                profile, _ = Profile.objects.get_or_create(user=u_obj)

        if not profile:
            messages.error(request, "Selected user profile was not found.")
            return redirect(next_url or reverse('platform_admin:clan-detail', kwargs={'pk': clan.pk}))

        clan.managers.add(profile)
        clan.restricted_users.remove(profile)

        if not profile.user.is_data_agent:
            profile.user.is_data_agent = True
            profile.user.save(update_fields=['is_data_agent'])

        messages.success(
            request,
            f"Granted full management & data input access for '{clan.name}' to {profile.user.first_name or profile.user.username} ({profile.user.email})."
        )
        return redirect(next_url or reverse('platform_admin:clan-detail', kwargs={'pk': clan.pk}))

    return redirect(next_url or reverse('platform_admin:clan-detail', kwargs={'pk': clan.pk}))


@login_required
def clan_revoke_access_view(request, pk, profile_id):
    """
    Revoke a user's manager access for this clan.
    """
    clan = get_object_or_404(Clan, id=pk, is_deleted=False)

    if not can_user_manage_clan(request.user, clan):
        messages.error(request, "You do not have permission to revoke access for this clan.")
        return redirect('platform_admin:clan-detail', pk=clan.pk)

    profile = get_object_or_404(Profile, id=profile_id)
    clan.managers.remove(profile)

    messages.info(
        request,
        f"Revoked management access for '{clan.name}' from {profile.user.first_name or profile.user.username}."
    )
    return redirect('platform_admin:clan-detail', pk=clan.pk)
