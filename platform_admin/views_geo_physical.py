from django.shortcuts import render, redirect, reverse
from django.contrib.auth.decorators import login_required
from accounts.models import Account, Profile
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.contrib import messages
from django.conf import settings
from .forms import MarketSectorForm, MarketSectorBulkDataForm, GeoPhysicalForm, GeoPhysicalGeoPoliticalZoneForm, GeoPhysicalStateForm, GeoPhysicalCityForm, GeoPhysicalClanForm
from .models import MarketSectorBulkData, MarketSector, Historical, GeoPhysicalData, GeoPhysicalCategory
from .tasks import create_new_customers
from utility.models import Country, State, GeoPoliticalZone, City, Clan
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.views.generic import ( ListView, DetailView, CreateView, 
                                    UpdateView, DeleteView, RedirectView, View, TemplateView)

from .forms_update import (
    GeoPhysicalGeoPoliticalZoneUpdateForm,
    GeoPhysicalStateUpdateForm,
    GeoPhysicalCityUpdateForm,
    GeoPhysicalClanUpdateForm,
    GeoPhysicalDeleteDataForm
    )

@login_required
def geo_physical_detail_view(request, pk):
    object = GeoPhysicalData.my_objects.get(id=pk)

    if object.clan:
        form = GeoPhysicalClanUpdateForm(request.POST or None, request.FILES or None, instance=object)

        if request.htmx:
            template_name = 'platform_admin/geo_physical/partials/ajax_geo_physical_update.html'

        if form.is_valid():
            clan = form.instance.clan
            form.instance.geo_political_zone = clan.city.state.geo_political_zone
            form.instance.state = clan.city.state
            form.instance.city = clan.city
            form.save()
            messages.success(request, "Data added successfully!!!")
            return HttpResponseRedirect(reverse('platform_admin:geo-physical-detail-view', kwargs={'pk': pk} ))
        return render(request, 'platform_admin/geo_physical/geo-physical-detail.html', context = {'object': object, 'form': form})

    if object.city:
        form = GeoPhysicalCityUpdateForm(request.POST or None, request.FILES or None, instance=object)

        if request.htmx:
            template_name = 'platform_admin/geo_physical/partials/ajax_geo_physical_update.html'

        if form.is_valid():
            city = form.instance.city
            form.instance.geo_political_zone = city.state.geo_political_zone
            form.instance.state = city.state
            form.save()
            messages.success(request, "Data added successfully!!!")
            return HttpResponseRedirect(reverse('platform_admin:geo-physical-detail-view', kwargs={'pk': pk} ))
        return render(request, 'platform_admin/geo_physical/geo-physical-detail.html', context = {'object': object, 'form': form})

    if object.state:
        form = GeoPhysicalStateUpdateForm(request.POST or None, request.FILES or None, instance=object)

        if request.htmx:
            template_name = 'platform_admin/geo_physical/partials/ajax_geo_physical_update.html'

        if form.is_valid():
            state = form.instance.state
            form.instance.geo_political_zone = state.geo_political_zone
            form.save()
            messages.success(request, "Data added successfully!!!")
            return HttpResponseRedirect(reverse('platform_admin:geo-physical-detail-view', kwargs={'pk': pk} ))
        return render(request, 'platform_admin/geo_physical/geo-physical-detail.html', context = {'object': object, 'form': form})

    if object.geo_political_zone:
        form = GeoPhysicalGeoPoliticalZoneUpdateForm(request.POST or None, request.FILES or None, instance=object)

        if request.htmx:
            template_name = 'platform_admin/geo_physical/partials/ajax_geo_physical_update.html'

        if form.is_valid():
            form.save()
            messages.success(request, "Data added successfully!!!")
            return HttpResponseRedirect(reverse('platform_admin:geo-physical-detail-view', kwargs={'pk': pk} ))
        return render(request, 'platform_admin/geo_physical/geo-physical-detail.html', context = {'object': object, 'form': form})

    return render(request, 'platform_admin/geo_physical/geo-physical-detail.html')

@login_required
def geo_physical_delete_data(request, pk):
    geo_physical_object = GeoPhysicalData.my_objects.get(id=pk)
    form = GeoPhysicalDeleteDataForm(request.POST or None, request.FILES or None, instance=geo_physical_object)
        
    if request.method == 'POST':
        form = GeoPhysicalDeleteDataForm(request.POST or None, request.FILES or None, instance=geo_physical_object)
        if form.is_valid():
            geo_physical_object.is_deleted = True
            form.save()
            return redirect("platform_admin:geo-physical-data-list-view")
            print("COMPLETED!!!")
    else:
        form = GeoPhysicalDeleteDataForm(request.POST or None, request.FILES or None, instance=geo_physical_object)
    context = {
        "form": form
    }
    return render(request, 'platform_admin/geo_physical/geo-physical-delete.html', context)



@login_required
def geo_physical_list_view(request):
    geo_physicals = _load_geo_physicals(request)
    # objects = MarketSector.objects.all().order_by('-date_created')
    context = {
        'geo_physicals': geo_physicals,
    }
    return render(request, 'platform_admin/geo_physical/all-geo-physicals.html', context)


@login_required
def list_load_geo_physicals_view(request):
    geo_physical = _load_geo_physicals(request)
    context = {"geo_physicals": geo_physical,}
    return render(request, "platform_admin/geo_physical/partials/all-geo-physicals.html", context)

def _load_geo_physicals(request):
    page = request.GET.get("page")
    geo_physicals = GeoPhysicalData.my_objects.all().order_by('-date_created')
    paginator = Paginator(geo_physicals, 20)
    try:
        geo_physicals = paginator.page(page)
    except PageNotAnInteger:
        geo_physicals = paginator.page(1)
    except EmptyPage:
        geo_physicals = paginator.page(paginator.num_pages)
    return geo_physicals




################## BEGINNING OF VARIOUS LOCATION DATA ENTRY CENTERS ###########################################
@login_required
def geo_physical_create_view(request):
    form = GeoPhysicalForm(request.POST or None, request.FILES or None)

    if request.htmx:
        template_name = 'platform_admin/geo_physical/partials/ajax_geo_physical_create.html'

    if form.is_valid():
        nigeria_as_country_location = Country.my_objects.get(id=1)

        form.instance.user = request.user.account_profile
        form.instance.country = nigeria_as_country_location
        newly_saved_form = form.save()
        # messages.success(request, "Data added successfully!!!")
        # return HttpResponseRedirect(reverse('platform_admin:market-sector-create-view'))

    context = {
    'form': form,
    }
    return render(request, 'platform_admin/geo_physical/geo-physical-create.html', context)


@login_required
def geo_physical_geo_political_zone_create_view(request, geozone_pk):
    geo_political_zone = GeoPoliticalZone.my_objects.get(id=geozone_pk)
    form = GeoPhysicalGeoPoliticalZoneForm(request.POST or None, request.FILES or None)

    if request.htmx:
        template_name = 'platform_admin/geo_physical/partials/geo-physical-geo-political-zone-create.html'

    if form.is_valid():
        nigeria_as_country_location = Country.my_objects.get(id=1)

        form.instance.user = request.user.account_profile
        form.instance.country = nigeria_as_country_location
        form.instance.geo_political_zone = geo_political_zone
        newly_saved_form = form.save()
        # messages.success(request, "Data added successfully!!!")
        # return HttpResponseRedirect(reverse('platform_admin:market-sector-create-view'))

    context = {
    'form': form,
    'object': geo_political_zone,
    }
    return render(request, 'platform_admin/geo_physical/geo-physical-geo-political-zone-create.html', context)


@login_required
def geo_physical_state_create_view(request, state_location_pk):
    state = State.my_objects.get(id=state_location_pk)
    form = GeoPhysicalStateForm(request.POST or None, request.FILES or None)

    if request.htmx:
        template_name = 'platform_admin/geo_physical/partials/geo-physical-state-create.html'

    if form.is_valid():
        nigeria_as_country_location = Country.my_objects.get(id=1)

        form.instance.user = request.user.account_profile
        form.instance.country = nigeria_as_country_location
        form.instance.geo_political_zone = state.geo_political_zone
        form.instance.state = state
        newly_saved_form = form.save()
        # messages.success(request, "Data added successfully!!!")
        # return HttpResponseRedirect(reverse('platform_admin:market-sector-create-view'))

    context = {
    'form': form,
    'object': state,
    }
    return render(request, 'platform_admin/geo_physical/geo-physical-state-create.html', context)


@login_required
def geo_physical_city_create_view(request, city_location_pk):
    city = City.my_objects.get(id=city_location_pk)
    form = GeoPhysicalCityForm(request.POST or None, request.FILES or None)

    if request.htmx:
        template_name = 'platform_admin/geo_physical/partials/geo-physical-city-create.html'

    if form.is_valid():
        nigeria_as_country_location = Country.my_objects.get(id=1)

        form.instance.user = request.user.account_profile
        form.instance.country = nigeria_as_country_location
        form.instance.geo_political_zone = city.state.geo_political_zone
        form.instance.state = city.state
        form.instance.city = city
        newly_saved_form = form.save()
        # messages.success(request, "Data added successfully!!!")
        # return HttpResponseRedirect(reverse('platform_admin:market-sector-create-view'))

    context = {
    'form': form,
    'object': city,
    }
    return render(request, 'platform_admin/geo_physical/geo-physical-city-create.html', context)


@login_required
def geo_physical_clan_create_view(request, clan_location_pk):
    clan = Clan.my_objects.get(id=clan_location_pk)
    user_profile = request.user.account_profile
    is_authorized = (
        request.user.is_admin
        or request.user.is_superuser
        or user_profile in clan.managers.all()
        or (clan.city and user_profile in clan.city.managers.all())
    ) and (user_profile not in clan.restricted_users.all())

    if not is_authorized:
        messages.error(request, f"You do not have permission to input data for {clan.name} Clan.")
        return redirect('platform_admin:dashboard')

    form = GeoPhysicalClanForm(request.POST or None, request.FILES or None)

    if request.htmx:
        template_name = 'platform_admin/geo_physical/partials/geo-physical-clan-create.html'

    if form.is_valid():
        nigeria_as_country_location = Country.my_objects.first() or Country.objects.first()

        form.instance.user = user_profile
        form.instance.country = nigeria_as_country_location
        if clan.city and clan.city.state:
            form.instance.geo_political_zone = clan.city.state.geo_political_zone
            form.instance.state = clan.city.state
            form.instance.city = clan.city
        elif clan.state:
            form.instance.geo_political_zone = clan.geo_political_zone or (clan.state.geo_political_zone if clan.state else None)
            form.instance.state = clan.state
            form.instance.city = clan.city
        form.instance.clan = clan
        newly_saved_form = form.save()
        messages.success(request, f"Geo-physical data added successfully for {clan.name} Clan!")
        return redirect('platform_admin:geo-physical-clan-create-view', clan_location_pk=clan.id)

    context = {
        'form': form,
        'object': clan,
    }
    return render(request, 'platform_admin/geo_physical/geo-physical-clan-create.html', context)

################## END OF VARIOUS LOCATION DATA ENTRY CENTERS ###########################################




@login_required
def geo_physical_data_list_view(request):
    geo_politicals = GeoPoliticalZone.my_objects.all().order_by('name')
    states = State.my_objects.all().order_by('name')
    cities = City.my_objects.all().order_by('name')
    categories = GeoPhysicalCategory.my_objects.all()
    context = {
        'geo_politicals': geo_politicals,
        'states' : states,
        'cities' : cities,
        'categories': categories,
    }
    return render(request, 'platform_admin/geo_physical/geo_physical-data-list-view.html', context)



########################### Beginning of GEO PHYSICAL Data List View With Search ######################################
@login_required
def geo_physical_data_list_view(request):
    geo_politicals = GeoPoliticalZone.my_objects.all().order_by('name')
    states = State.my_objects.all().order_by('name')
    geo_physicals, search = _search_geo_physical_data(request)
    categories = GeoPhysicalCategory.my_objects.all()
    context = {
        'geo_politicals': geo_politicals,
        'states' : states,
        # 'geo_physicals': geo_physicals,
        'categories': categories,
    }
    return render(request, 'platform_admin/geo_physical/geo_physical-data-list-view.html', context)


def list_search_geo_physical_data_view(request):
    geo_physicals, search = _search_geo_physical_data(request)
    context = {"geo_physicals": geo_physicals, "search": search}
    return render(request, "platform_admin/geo_physical/partials/search-all-geo-physical.html", context)

def _search_geo_physical_data(request):
    search = request.GET.get("search")
    page = request.GET.get("page")
    geo_physicals = GeoPhysicalData.my_objects.all().order_by('-id')
    
    if search:
        geo_physicals = geo_physicals.filter(description__icontains=search)

    paginator = Paginator(geo_physicals, 20)
    try:
        geo_physicals = paginator.page(page)
    except PageNotAnInteger:
        geo_physicals = paginator.page(1)
    except EmptyPage:
        geo_physicals = paginator.page(paginator.num_pages)

    return geo_physicals, search or ""


########################### End of GEO PHYSICAL Data List View With Search ######################################



###################################### BEGINNING OF LOGGED IN USER GEO_PHYSICAL DATA ###########################################
@login_required
def user_geo_physical_list_view(request):
    user_geo_physicals = _load_user_geo_physicals(request)
    # objects = MarketSector.objects.all().order_by('-date_created')
    context = {
        'user_geo_physicals': user_geo_physicals,
    }
    return render(request, 'platform_admin/geo_physical/user-geo-physicals.html', context)


@login_required
def list_load_user_geo_physicals_view(request):
    user_geo_physical = _load_user_geo_physicals(request)
    context = {"user_geo_physicals": user_geo_physical,}
    return render(request, "platform_admin/geo_physical/partials/user_geo_physicals.html", context)

def _load_user_geo_physicals(request):
    page = request.GET.get("page")
    user = request.user.account_profile
    user_geo_physicals = GeoPhysicalData.my_objects.filter(user=user).order_by('-date_created')
    paginator = Paginator(user_geo_physicals, 20)
    try:
        user_geo_physicals = paginator.page(page)
    except PageNotAnInteger:
        user_geo_physicals = paginator.page(1)
    except EmptyPage:
        user_geo_physicals = paginator.page(paginator.num_pages)
    return user_geo_physicals

###################################### END OF LOGGED IN USER GEO_PHYSICAL DATA ###########################################




###################################### BEGINNING OF GEOPOLITICAL ZONES FOR GEO_PHYSICAL DATA ###########################################
@login_required
def geo_physical_geo_zone_detail_view(request, geozone_pk):
    object = GeoPoliticalZone.my_objects.get(id=geozone_pk)
    geozone_pk = geozone_pk
    objects = _load_geo_physical_geo_zone_details(request, geozone_pk)
    context = {
        'object': object,
        'objects': objects,
        'states': State.my_objects.filter(geo_political_zone=object).order_by('name'),
    }
    return render(request, 'platform_admin/geo_physical/geo_physical-geo-zone-detail.html', context)



@login_required
def list_load_geo_physical_geo_zone_details_view(request, geozone_pk):
    object = GeoPoliticalZone.my_objects.get(id=geozone_pk)
    geo_physical_geo_zone_detail = _load_geo_physical_geo_zone_details(request, geozone_pk)
    context = {"objects": geo_physical_geo_zone_detail, 'object': object}
    return render(request, "platform_admin/geo_physical/partials/geo_physical_geo_zone_details.html", context)



@login_required
def _load_geo_physical_geo_zone_details(request, geozone_pk):
    page = request.GET.get("page")
    geo_physical_geo_zone_details = GeoPhysicalData.my_objects.filter(geo_political_zone=geozone_pk).order_by('-date_created')
    paginator = Paginator(geo_physical_geo_zone_details, 20)
    try:
        geo_physical_geo_zone_details = paginator.page(page)
    except PageNotAnInteger:
        geo_physical_geo_zone_details = paginator.page(1)
    except EmptyPage:
        geo_physical_geo_zone_details = paginator.page(paginator.num_pages)
    return geo_physical_geo_zone_details

###################################### END OF GEOPOLITICAL ZONES FOR GEO_PHYSICAL DATA ###########################################


###################################### BEGINNING OF STATES LOCATION FOR GEO_PHYSICAL DATA ###########################################
@login_required
def geo_physical_state_location_detail_view(request, state_location_pk):
    object = State.my_objects.get(id=state_location_pk)
    state_location_pk = state_location_pk
    objects = _load_geo_physical_state_location_details(request, state_location_pk)
    context = {
        'object': object,
        'objects': objects,
        'cities': City.my_objects.filter(state=object).order_by('name'),
    }
    return render(request, 'platform_admin/geo_physical/geo_physical-state-location-detail.html', context)



@login_required
def list_load_geo_physical_state_location_details_view(request, state_location_pk):
    object = State.my_objects.get(id=state_location_pk)
    geo_physical_state_location_detail = _load_geo_physical_state_location_details(request, state_location_pk)
    context = {"objects": geo_physical_state_location_detail, 'object': object}
    return render(request, "platform_admin/geo_physical/partials/geo_physical_state_location_details.html", context)



@login_required
def _load_geo_physical_state_location_details(request, state_location_pk):
    page = request.GET.get("page")
    geo_physical_state_location_details = GeoPhysicalData.my_objects.filter(state=state_location_pk).order_by('-date_created')
    paginator = Paginator(geo_physical_state_location_details, 20)
    try:
        geo_physical_state_location_details = paginator.page(page)
    except PageNotAnInteger:
        geo_physical_state_location_details = paginator.page(1)
    except EmptyPage:
        geo_physical_state_location_details = paginator.page(paginator.num_pages)
    return geo_physical_state_location_details

###################################### END OF STATES LOCATION FOR GEO_PHYSICAL DATA ###########################################



###################################### BEGINNING OF CITIES LOCATION FOR GEO_PHYSICAL DATA ###########################################

@login_required
def geo_physical_city_location_detail_view(request, city_location_pk):
    object = City.my_objects.get(id=city_location_pk)
    city_location_pk = city_location_pk
    objects = _load_geo_physical_city_location_details(request, city_location_pk)
    context = {
        'object': object,
        'objects': objects,
        'clans': Clan.my_objects.filter(city=object).order_by('name'),
    }
    return render(request, 'platform_admin/geo_physical/geo_physical-city-location-detail.html', context)



@login_required
def list_load_geo_physical_city_location_details_view(request, city_location_pk):
    object = City.my_objects.get(id=city_location_pk)
    geo_physical_city_location_detail = _load_geo_physical_city_location_details(request, city_location_pk)
    context = {"objects": geo_physical_city_location_detail, 'object': object}
    return render(request, "platform_admin/geo_physical/partials/geo_physical_city_location_details.html", context)



@login_required
def _load_geo_physical_city_location_details(request, city_location_pk):
    page = request.GET.get("page")
    geo_physical_city_location_details = GeoPhysicalData.my_objects.filter(city=city_location_pk).order_by('-date_created')
    paginator = Paginator(geo_physical_city_location_details, 20)
    try:
        geo_physical_city_location_details = paginator.page(page)
    except PageNotAnInteger:
        geo_physical_city_location_details = paginator.page(1)
    except EmptyPage:
        geo_physical_city_location_details = paginator.page(paginator.num_pages)
    return geo_physical_city_location_details

###################################### END OF CITIES LOCATION FOR GEO_PHYSICAL DATA ###########################################


###################################### BEGINNING OF CLANS LOCATION FOR GEO_PHYSICAL DATA ###########################################


@login_required
def geo_physical_clan_location_detail_view(request, clan_location_pk):
    object = Clan.my_objects.get(id=clan_location_pk)
    clan_location_pk = clan_location_pk
    objects = _load_geo_physical_clan_location_details(request, clan_location_pk)
    context = {
        'object': object,
        'objects': objects,
    }
    return render(request, 'platform_admin/geo_physical/geo_physical-clan-location-detail.html', context)



@login_required
def list_load_geo_physical_clan_location_details_view(request, clan_location_pk):
    object = Clan.my_objects.get(id=clan_location_pk)
    geo_physical_clan_location_detail = _load_geo_physical_clan_location_details(request, clan_location_pk)
    context = {"objects": geo_physical_clan_location_detail, 'object': object}
    return render(request, "platform_admin/geo_physical/partials/geo_physical_clan_location_details.html", context)



@login_required
def _load_geo_physical_clan_location_details(request, clan_location_pk):
    page = request.GET.get("page")
    geo_physical_clan_location_details = GeoPhysicalData.my_objects.filter(clan=clan_location_pk).order_by('-date_created')
    paginator = Paginator(geo_physical_clan_location_details, 20)
    try:
        geo_physical_clan_location_details = paginator.page(page)
    except PageNotAnInteger:
        geo_physical_clan_location_details = paginator.page(1)
    except EmptyPage:
        geo_physical_clan_location_details = paginator.page(paginator.num_pages)
    return geo_physical_clan_location_details

###################################### END OF CLANS LOCATION FOR GEO_PHYSICAL DATA ###########################################



###################################### BEGINNING OF Category FOR GEO_PHYSICAL DATA ###########################################
@login_required
def geo_physical_category_detail_view(request, category_pk):
    object = GeoPhysicalCategory.my_objects.get(id=category_pk)
    category_pk = category_pk
    objects = _load_geo_physical_category_details(request, category_pk)
    context = {
        'object': object,
        'objects': objects,
        # 'market_sectors': Account.objects.all()
    }
    return render(request, 'platform_admin/geo_physical/geo_physical-category-detail.html', context)


@login_required
def list_load_geo_physical_category_details_view(request, category_pk):
    object = GeoPhysicalCategory.my_objects.get(id=category_pk)
    geo_physical_category_detail = _load_geo_physical_category_details(request, category_pk)
    context = {"objects": geo_physical_category_detail, 'object': object}
    return render(request, "platform_admin/geo_physical/partials/geo_physical_category_details.html", context)

@login_required
def _load_geo_physical_category_details(request, category_pk):
    page = request.GET.get("page")
    geo_physical_category_details = GeoPhysicalData.my_objects.filter(category=category_pk).order_by('-date_created')
    paginator = Paginator(geo_physical_category_details, 2)
    try:
        geo_physical_category_details = paginator.page(page)
    except PageNotAnInteger:
        geo_physical_category_details = paginator.page(1)
    except EmptyPage:
        geo_physical_category_details = paginator.page(paginator.num_pages)
    return geo_physical_category_details


###################################### END OF Category FOR GEO_PHYSICAL DATA ###########################################