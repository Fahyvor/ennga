from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Q
from accounts.models import Account, Profile
from utility.models import Clan, SubClan, State, City, GeoPoliticalZone, NODE_TYPE_CHOICES
from platform_admin.forms_clan import ClanForm, SubClanForm


def is_platform_admin(user):
    return user.is_authenticated and (user.is_admin or user.is_staff or user.is_superuser)


@login_required
def clan_access_list_view(request):
    if not is_platform_admin(request.user):
        messages.error(request, "Access denied. Only platform administrators can manage clan permissions.")
        return redirect('platform_admin:dashboard')

    query = request.GET.get('q', '').strip()
    filter_type = request.GET.get('filter_type', 'all')

    clans = Clan.objects.filter(is_deleted=False).select_related('city', 'state', 'geo_political_zone').prefetch_related('managers__user', 'restricted_users__user')
    subclans = SubClan.objects.filter(is_deleted=False).select_related('clan', 'city', 'state').prefetch_related('managers__user')
    users = Account.objects.filter(is_active=True).select_related('account_profile').order_by('first_name', 'username')

    if query:
        clans = clans.filter(
            Q(name__icontains=query) |
            Q(city__name__icontains=query) |
            Q(state__name__icontains=query) |
            Q(managers__user__username__icontains=query) |
            Q(managers__user__email__icontains=query)
        ).distinct()

        subclans = subclans.filter(
            Q(name__icontains=query) |
            Q(clan__name__icontains=query) |
            Q(managers__user__username__icontains=query) |
            Q(managers__user__email__icontains=query)
        ).distinct()

    # Collect active assignments
    clan_assignments = []
    for clan in clans:
        for mgr in clan.managers.all():
            clan_assignments.append({
                'type': 'Clan',
                'target_name': clan.name,
                'location': f"{clan.city.name if clan.city else ''}, {clan.state.name if clan.state else ''}".strip(', '),
                'profile': mgr,
                'clan_id': clan.id,
                'subclan_id': None,
                'historical_url': reverse('platform_admin:historical-clan-create-view', kwargs={'clan_location_pk': clan.id}),
                'market_url': reverse('platform_admin:market-sector-clan-create-view', kwargs={'clan_location_pk': clan.id}),
                'geophysical_url': reverse('platform_admin:geo-physical-clan-create-view', kwargs={'clan_location_pk': clan.id}),
            })

    subclan_assignments = []
    for sc in subclans:
        for mgr in sc.managers.all():
            subclan_assignments.append({
                'type': 'Sub-Clan',
                'target_name': f"{sc.name} ({sc.clan.name if sc.clan else ''})",
                'location': f"{sc.city.name if sc.city else ''}, {sc.state.name if sc.state else ''}".strip(', '),
                'profile': mgr,
                'clan_id': sc.clan.id if sc.clan else None,
                'subclan_id': sc.id,
                'historical_url': reverse('platform_admin:historical-clan-create-view', kwargs={'clan_location_pk': sc.clan.id}) if sc.clan else "#",
                'market_url': reverse('platform_admin:market-sector-clan-create-view', kwargs={'clan_location_pk': sc.clan.id}) if sc.clan else "#",
                'geophysical_url': reverse('platform_admin:geo-physical-clan-create-view', kwargs={'clan_location_pk': sc.clan.id}) if sc.clan else "#",
            })

    all_assignments = clan_assignments + subclan_assignments

    # Stats
    total_clans_count = Clan.objects.filter(is_deleted=False).count()
    total_subclans_count = SubClan.objects.filter(is_deleted=False).count()
    assigned_users_count = len(set([a['profile'].id for a in all_assignments]))

    all_clans_dropdown = Clan.objects.filter(is_deleted=False).order_by('name')
    all_subclans_dropdown = SubClan.objects.filter(is_deleted=False).select_related('clan').order_by('name')
    all_states = State.objects.filter(is_deleted=False).order_by('name')

    context = {
        'clans': clans,
        'subclans': subclans,
        'users': users,
        'all_assignments': all_assignments,
        'total_clans_count': total_clans_count,
        'total_subclans_count': total_subclans_count,
        'assigned_users_count': assigned_users_count,
        'all_clans_dropdown': all_clans_dropdown,
        'all_subclans_dropdown': all_subclans_dropdown,
        'all_states': all_states,
        'node_type_choices': NODE_TYPE_CHOICES,
        'clan_create_form': ClanForm(),
        'subclan_create_form': SubClanForm(),
        'query': query,
        'filter_type': filter_type,
    }
    return render(request, 'platform_admin/clan_access_management.html', context)


@login_required
def grant_clan_access_view(request):
    if not is_platform_admin(request.user):
        return HttpResponseForbidden("Only administrators can grant clan access.")

    if request.method == "POST":
        profile_id = request.POST.get("profile_id")
        clan_id = request.POST.get("clan_id")
        next_url = request.POST.get("next", "")

        if not profile_id or not clan_id:
            messages.error(request, "Please select both a user and a clan.")
            return redirect(next_url or 'platform_admin:clan-access-management')

        profile = get_object_or_404(Profile, id=profile_id)
        clan = get_object_or_404(Clan, id=clan_id)

        # Grant access
        clan.managers.add(profile)
        clan.restricted_users.remove(profile)

        # Ensure user has data agent capability enabled
        if not profile.user.is_data_agent:
            profile.user.is_data_agent = True
            profile.user.save(update_fields=['is_data_agent'])

        messages.success(
            request, 
            f"Granted data input access to {profile.user.first_name or profile.user.username} ({profile.user.email}) for clan '{clan.name}'."
        )

        if next_url:
            return redirect(next_url)
        return redirect('platform_admin:clan-access-management')

    return redirect('platform_admin:clan-access-management')


@login_required
def revoke_clan_access_view(request, clan_id, profile_id):
    if not is_platform_admin(request.user):
        return HttpResponseForbidden("Only administrators can revoke clan access.")

    clan = get_object_or_404(Clan, id=clan_id)
    profile = get_object_or_404(Profile, id=profile_id)

    clan.managers.remove(profile)
    messages.info(
        request, 
        f"Revoked data input access for clan '{clan.name}' from {profile.user.first_name or profile.user.username}."
    )

    next_url = request.GET.get("next") or request.META.get('HTTP_REFERER')
    if next_url:
        return redirect(next_url)
    return redirect('platform_admin:clan-access-management')


@login_required
def grant_subclan_access_view(request):
    if not is_platform_admin(request.user):
        return HttpResponseForbidden("Only administrators can grant sub-clan access.")

    if request.method == "POST":
        profile_id = request.POST.get("profile_id")
        subclan_id = request.POST.get("subclan_id")
        next_url = request.POST.get("next", "")

        if not profile_id or not subclan_id:
            messages.error(request, "Please select both a user and a sub-clan.")
            return redirect(next_url or 'platform_admin:clan-access-management')

        profile = get_object_or_404(Profile, id=profile_id)
        subclan = get_object_or_404(SubClan, id=subclan_id)

        subclan.managers.add(profile)
        subclan.restricted_users.remove(profile)

        if not profile.user.is_data_agent:
            profile.user.is_data_agent = True
            profile.user.save(update_fields=['is_data_agent'])

        messages.success(
            request, 
            f"Granted data input access to {profile.user.first_name or profile.user.username} for sub-clan '{subclan.name}'."
        )

        if next_url:
            return redirect(next_url)
        return redirect('platform_admin:clan-access-management')

    return redirect('platform_admin:clan-access-management')


@login_required
def revoke_subclan_access_view(request, subclan_id, profile_id):
    if not is_platform_admin(request.user):
        return HttpResponseForbidden("Only administrators can revoke sub-clan access.")

    subclan = get_object_or_404(SubClan, id=subclan_id)
    profile = get_object_or_404(Profile, id=profile_id)

    subclan.managers.remove(profile)
    messages.info(
        request, 
        f"Revoked data input access for sub-clan '{subclan.name}' from {profile.user.first_name or profile.user.username}."
    )

    next_url = request.GET.get("next") or request.META.get('HTTP_REFERER')
    if next_url:
        return redirect(next_url)
    return redirect('platform_admin:clan-access-management')


@login_required
def api_load_subclans_for_clan_view(request):
    clan_id = request.GET.get('clan_id')
    if not clan_id:
        return JsonResponse({'subclans': []})

    subclans = SubClan.objects.filter(clan_id=clan_id, is_deleted=False).order_by('name')
    data = [{
        'id': sc.id,
        'name': sc.name,
        'node_id': sc.display_node_id,
        'node_type': sc.get_node_type_display() if hasattr(sc, 'get_node_type_display') else sc.node_type,
    } for sc in subclans]
    return JsonResponse({'subclans': data})


@login_required
def api_generate_node_id_view(request):
    """
    API endpoint that returns the next sequential PRD Node ID for a given clan and node_type.
    """
    clan_id = request.GET.get('clan_id')
    node_type = request.GET.get('node_type', 'STREET')

    if not clan_id:
        return JsonResponse({'node_id': '', 'status': 'error', 'message': 'Missing clan_id'})

    clan = Clan.objects.filter(id=clan_id, is_deleted=False).first()
    if not clan:
        return JsonResponse({'node_id': '', 'status': 'error', 'message': 'Clan not found'})

    mock_subclan = SubClan(clan=clan, node_type=node_type)
    generated_id = mock_subclan.generate_next_node_id()
    return JsonResponse({
        'status': 'success',
        'node_id': generated_id,
        'generated_node_id': generated_id,
        'clan_name': clan.name,
        'territory_code': clan.code or (clan.display_node_id.split('-')[0] if clan.display_node_id else 'NOD'),
        'node_type': node_type,
    })
