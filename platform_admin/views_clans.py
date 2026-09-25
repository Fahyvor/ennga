from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from django.db.models import Q, Count
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.urls import reverse

from accounts.models import Account, Profile
from utility.models import Clan, SubClan, State, City, GeoPoliticalZone, Country
from platform_admin.models import Historical, MarketSector, GeoPhysicalData
from .forms_clan import ClanForm, SubClanForm


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


@login_required
def clan_list_view(request):
    """
    Directory & listing of all Clans with search, state filtering,
    view modes ('all', 'my', 'subclans'), and pagination.
    """
    query = request.GET.get('q', '').strip()
    state_id = request.GET.get('state', '').strip()
    view_mode = request.GET.get('view_mode', 'all')
    page = request.GET.get('page', 1)

    user_profile = getattr(request.user, 'account_profile', None)
    admin_user = is_platform_admin(request.user)

    # Base QuerySets
    clans_qs = Clan.objects.filter(is_deleted=False).select_related(
        'city', 'state', 'geo_political_zone'
    ).prefetch_related('managers__user')

    subclans_qs = SubClan.objects.filter(is_deleted=False).select_related(
        'clan', 'city', 'state'
    ).prefetch_related('managers__user')

    # Counts
    total_clans_count = Clan.objects.filter(is_deleted=False).count()
    total_subclans_count = SubClan.objects.filter(is_deleted=False).count()
    
    my_clans_count = 0
    if user_profile:
        my_clans_count = Clan.objects.filter(
            Q(managers=user_profile) | Q(city__managers=user_profile),
            is_deleted=False
        ).exclude(restricted_users=user_profile).distinct().count()

    # Filter by view_mode
    if view_mode == 'my' and user_profile:
        clans_qs = clans_qs.filter(
            Q(managers=user_profile) | Q(city__managers=user_profile)
        ).exclude(restricted_users=user_profile).distinct()

    # Filter by State
    if state_id:
        clans_qs = clans_qs.filter(state_id=state_id)
        subclans_qs = subclans_qs.filter(state_id=state_id)

    # Search Filter
    if query:
        clans_qs = clans_qs.filter(
            Q(name__icontains=query) |
            Q(city__name__icontains=query) |
            Q(state__name__icontains=query) |
            Q(geo_political_zone__name__icontains=query) |
            Q(managers__user__first_name__icontains=query) |
            Q(managers__user__last_name__icontains=query) |
            Q(managers__user__username__icontains=query) |
            Q(managers__user__email__icontains=query)
        ).distinct()

        subclans_qs = subclans_qs.filter(
            Q(name__icontains=query) |
            Q(clan__name__icontains=query) |
            Q(city__name__icontains=query) |
            Q(state__name__icontains=query) |
            Q(managers__user__username__icontains=query) |
            Q(managers__user__email__icontains=query)
        ).distinct()

    # Annotate sub-clans count
    clans_qs = clans_qs.annotate(
        subclans_count=Count('subclan', filter=Q(subclan__is_deleted=False))
    ).order_by('name')

    # Pagination
    if view_mode == 'subclans':
        subclans_qs = subclans_qs.order_by('name')
        paginator = Paginator(subclans_qs, 40)
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
        try:
            page_obj = paginator.page(page)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
        clans_page = page_obj
        subclans_page = None

    all_states = State.objects.filter(is_deleted=False).order_by('name')
    all_clans_dropdown = Clan.objects.filter(is_deleted=False).order_by('name')
    clan_create_form = ClanForm()

    context = {
        'clans': clans_page,
        'subclans': subclans_page,
        'page_obj': page_obj,
        'total_clans_count': total_clans_count,
        'total_subclans_count': total_subclans_count,
        'my_clans_count': my_clans_count,
        'query': query,
        'state_id': state_id,
        'view_mode': view_mode,
        'all_states': all_states,
        'all_clans_dropdown': all_clans_dropdown,
        'node_type_choices': NODE_TYPE_CHOICES,
        'clan_create_form': clan_create_form,
        'is_admin': admin_user,
    }
    return render(request, 'platform_admin/clans/clan_list.html', context)


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
    subclans = clan.subclan_set.filter(is_deleted=False).select_related(
        'city', 'state'
    ).prefetch_related('managers__user').order_by('name')

    # Data records under this clan
    historical_records = Historical.objects.filter(clan=clan, is_deleted=False).select_related('category').order_by('-date_created')[:15]
    historical_count = Historical.objects.filter(clan=clan, is_deleted=False).count()

    market_records = MarketSector.objects.filter(clan=clan, is_deleted=False).select_related('category', 'sub_category').order_by('-date_created')[:15]
    market_count = MarketSector.objects.filter(clan=clan, is_deleted=False).count()

    geo_records = GeoPhysicalData.objects.filter(clan=clan, is_deleted=False).select_related('category').order_by('-date_created')[:15]
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

    context = {
        'clan': clan,
        'can_manage': can_manage,
        'is_admin': is_admin,
        'subclans': subclans,
        'subclans_count': subclans.count(),
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

    if not is_platform_admin(request.user):
        messages.error(request, "Only platform administrators can delete clans.")
        return redirect('platform_admin:clan-detail', pk=clan.pk)

    if request.method == "POST":
        clan.is_deleted = True
        clan.save(update_fields=['is_deleted'])
        messages.info(request, f"Clan '{clan.name}' has been archived/deleted.")
        return redirect('platform_admin:clan-list')

    return redirect('platform_admin:clan-detail', pk=clan.pk)


@login_required
def subclan_create_for_clan_view(request, clan_id):
    """
    Add a new Sub-Clan directly under a parent Clan.
    Follows PRD Node ID convention: [Territory]-[Node Type]-[Sequential Number]
    """
    clan = get_object_or_404(Clan, id=clan_id, is_deleted=False)
    next_url = request.POST.get('next', '').strip()

    if not can_user_manage_clan(request.user, clan):
        messages.error(request, f"You do not have permission to add sub-nodes to '{clan.name}' Clan.")
        return redirect(next_url or reverse('platform_admin:clan-detail', kwargs={'pk': clan.pk}))

    if request.method == "POST":
        name = request.POST.get('name', '').strip()
        node_type = request.POST.get('node_type', 'STREET').strip() or 'STREET'
        node_id = request.POST.get('node_id', '').strip()

        if not name:
            messages.error(request, "Sub-clan / Node name is required.")
            return redirect(next_url or reverse('platform_admin:clan-detail', kwargs={'pk': clan.pk}))

        city_id = request.POST.get('city') or (clan.city.id if clan.city else None)
        state_id = request.POST.get('state') or (clan.state.id if clan.state else None)

        city = City.objects.filter(id=city_id).first() if city_id else clan.city
        state = State.objects.filter(id=state_id).first() if state_id else (city.state if city else clan.state)
        geo_zone = (state.geo_political_zone if state else clan.geo_political_zone)

        subclan = SubClan(
            name=name,
            clan=clan,
            node_type=node_type,
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

        messages.success(request, f"Node '{subclan.name}' [{subclan.display_node_id}] created successfully under '{clan.name}'.")
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
        node_type = request.POST.get('node_type', 'STREET').strip() or 'STREET'
        node_id = request.POST.get('node_id', '').strip()

        if not name:
            messages.error(request, "Node name is required.")
            return redirect(next_url or 'platform_admin:dashboard')

        city_id = request.POST.get('city') or (clan.city.id if clan.city else None)
        state_id = request.POST.get('state') or (clan.state.id if clan.state else None)
        city = City.objects.filter(id=city_id).first() if city_id else clan.city
        state = State.objects.filter(id=state_id).first() if state_id else (city.state if city else clan.state)
        geo_zone = (state.geo_political_zone if state else clan.geo_political_zone)

        subclan = SubClan(
            name=name,
            clan=clan,
            node_type=node_type,
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

        messages.success(request, f"Territorial Node '{subclan.name}' [{subclan.display_node_id}] created successfully under '{clan.name}'.")
        return redirect(next_url or reverse('platform_admin:clan-detail', kwargs={'pk': clan.pk}))

    return redirect(next_url or 'platform_admin:dashboard')


@login_required
def subclan_edit_view(request, pk):
    """
    Edit a Sub-Clan.
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
            city_id = request.POST.get('city')
            state_id = request.POST.get('state')

            if city_id:
                subclan.city = City.objects.filter(id=city_id).first()
            if state_id:
                subclan.state = State.objects.filter(id=state_id).first()

            subclan.save()
            messages.success(request, f"Sub-Clan '{subclan.name}' updated successfully.")

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
