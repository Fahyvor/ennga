from django.shortcuts import render, redirect, reverse
from django.contrib.auth.decorators import login_required
from accounts.models import Account, Profile
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.contrib import messages
from django.conf import settings
from .forms import MarketSectorForm, MarketSectorBulkDataForm, MarketSectorGeoPoliticalZoneForm, MarketSectorStateForm, MarketSectorCityForm, MarketSectorClanForm
from .models import MarketSectorBulkData, MarketSector, Historical, MarketSectorCategory, MarketSectorSubCategory
from .tasks import create_new_customers
from utility.models import Country, State, GeoPoliticalZone, City, Clan
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.views.generic import ( ListView, DetailView, CreateView, 
                                    UpdateView, DeleteView, RedirectView, View, TemplateView)
from .forms_update import (MarketSectorUpdateForm,
                            MarketSectorGeoPoliticalZoneUpdateForm,
                            MarketSectorStateUpdateForm,
                            MarketSectorCityUpdateForm,
                            MarketSectorClanUpdateForm,
                            MarketSectorDeleteDataForm
                        )


@login_required
def market_sector_detail_view(request, pk):
    object = MarketSector.my_objects.get(id=pk)

    if object.clan:
        form = MarketSectorClanUpdateForm(request.POST or None, request.FILES or None, instance=object)

        if request.htmx:
            template_name = 'platform_admin/market_sector/partials/ajax_market_sector_update.html'

        if form.is_valid():
            clan = form.instance.clan
            form.instance.geo_political_zone = clan.city.state.geo_political_zone
            form.instance.state = clan.city.state
            form.instance.city = clan.city
            form.save()
            messages.success(request, "Data added successfully!!!")
            return HttpResponseRedirect(reverse('platform_admin:market-sector-detail-view', kwargs={'pk': pk} ))
        return render(request, 'platform_admin/market_sector/market-sector-detail.html', context={'form': form, 'object': object,})

    if object.city:
        form = MarketSectorCityUpdateForm(request.POST or None, request.FILES or None, instance=object)

        if request.htmx:
            template_name = 'platform_admin/market_sector/partials/ajax_market_sector_update.html'

        if form.is_valid():
            city = form.instance.city
            form.instance.geo_political_zone = city.state.geo_political_zone
            form.instance.state = city.state
            form.save()
            messages.success(request, "Data added successfully!!!")
            return HttpResponseRedirect(reverse('platform_admin:market-sector-detail-view', kwargs={'pk': pk} ))
        return render(request, 'platform_admin/market_sector/market-sector-detail.html', context={'form': form, 'object': object,})

    if object.state:
        form = MarketSectorStateUpdateForm(request.POST or None, request.FILES or None, instance=object)

        if request.htmx:
            template_name = 'platform_admin/market_sector/partials/ajax_market_sector_update.html'

        if form.is_valid():
            state = form.instance.state
            form.instance.geo_political_zone = state.geo_political_zone
            form.save()
            messages.success(request, "Data added successfully!!!")
            return HttpResponseRedirect(reverse('platform_admin:market-sector-detail-view', kwargs={'pk': pk} ))
        return render(request, 'platform_admin/market_sector/market-sector-detail.html', context={'form': form, 'object': object,})

    if object.geo_political_zone:
        form = MarketSectorGeoPoliticalZoneUpdateForm(request.POST or None, request.FILES or None, instance=object)

        if request.htmx:
            template_name = 'platform_admin/market_sector/partials/ajax_market_sector_update.html'

        if form.is_valid():
            form.save()
            messages.success(request, "Data added successfully!!!")
            return HttpResponseRedirect(reverse('platform_admin:market-sector-detail-view', kwargs={'pk': pk} ))
        return render(request, 'platform_admin/market_sector/market-sector-detail.html', context={'form': form, 'object': object,})
    
    return render(request, 'platform_admin/market_sector/market-sector-detail.html')

@login_required
def market_sector_delete_data(request, pk):
    market_sector_object = MarketSector.my_objects.get(id=pk)
    form = MarketSectorDeleteDataForm(request.POST or None, request.FILES or None, instance=market_sector_object)

        
    if request.method == 'POST':
        form = MarketSectorDeleteDataForm(request.POST or None, request.FILES or None, instance=market_sector_object)
        if form.is_valid():
            market_sector_object.is_deleted = True
            form.save()
            return redirect("platform_admin:market-sector-data-list-view")
            print("COMPLETED!!!")
    else:
        form = MarketSectorDeleteDataForm(request.POST or None, request.FILES or None, instance=market_sector_object)
    context = {
        "form": form
    }
    return render(request, 'platform_admin/market_sector/market-sector-delete.html', context)

@login_required
def market_sector_list_view(request):
    market_sectors = _load_market_sectors(request)
    # objects = MarketSector.my_objects.all().order_by('-date_created')
    context = {
        'market_sectors': market_sectors,
    }
    return render(request, 'platform_admin/market_sector/all-market-sectors.html', context)


@login_required
def list_load_market_sectors_view(request):
    market_sector = _load_market_sectors(request)
    context = {"market_sectors": market_sector,}
    return render(request, "platform_admin/partials/all-market_sectors.html", context)

def _load_market_sectors(request):
    page = request.GET.get("page")
    market_sectors = MarketSector.my_objects.all().order_by('-date_created')
    paginator = Paginator(market_sectors, 50)
    try:
        market_sectors = paginator.page(page)
    except PageNotAnInteger:
        market_sectors = paginator.page(1)
    except EmptyPage:
        market_sectors = paginator.page(paginator.num_pages)
    return market_sectors



################## BEGINNING OF VARIOUS LOCATION DATA ENTRY CENTERS ###########################################
@login_required
def market_sector_create_view(request):
    form = MarketSectorForm(request.POST or None, request.FILES or None)

    if request.htmx:
        template_name = 'platform_admin/market_sector/partials/ajax_market_sector_create.html'

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
    return render(request, 'platform_admin/market-sector-create.html', context)


@login_required
def market_sector_geo_political_zone_create_view(request, geozone_pk):
    geo_political_zone = GeoPoliticalZone.my_objects.get(id=geozone_pk)
    form = MarketSectorGeoPoliticalZoneForm(request.POST or None, request.FILES or None)

    if request.htmx:
        template_name = 'platform_admin/market_sector/partials/market-sector-geo-political-zone-create.html'

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
    return render(request, 'platform_admin/market_sector/market-sector-geo-political-zone-create.html', context)


@login_required
def market_sector_state_create_view(request, state_location_pk):
    state = State.my_objects.get(id=state_location_pk)
    form = MarketSectorStateForm(request.POST or None, request.FILES or None)

    if request.htmx:
        template_name = 'platform_admin/market_sector/partials/market-sector-state-create.html'

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
    return render(request, 'platform_admin/market_sector/market-sector-state-create.html', context)


@login_required
def market_sector_city_create_view(request, city_location_pk):
    city = City.my_objects.get(id=city_location_pk)
    form = MarketSectorCityForm(request.POST or None, request.FILES or None)

    if request.htmx:
        template_name = 'platform_admin/market_sector/partials/market-sector-city-create.html'

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
    return render(request, 'platform_admin/market_sector/market-sector-city-create.html', context)


@login_required
def market_sector_clan_create_view(request, clan_location_pk):
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

    form = MarketSectorClanForm(request.POST or None, request.FILES or None)

    if request.htmx:
        template_name = 'platform_admin/market_sector/partials/market-sector-clan-create.html'

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
        messages.success(request, f"Market sector data added successfully for {clan.name} Clan!")
        return redirect('platform_admin:market-sector-clan-create-view', clan_location_pk=clan.id)

    context = {
        'form': form,
        'object': clan,
    }
    return render(request, 'platform_admin/market_sector/market-sector-clan-create.html', context)

################## END OF VARIOUS LOCATION DATA ENTRY CENTERS ###########################################



@login_required
def market_sector_upload_view(request):
    form_bulk = MarketSectorBulkDataForm(request.POST or None, request.FILES or None)

    if request.htmx:
        template_name = 'platform_admin/ajax_progress_bar_upload.html'

    if form_bulk.is_valid():
        nigeria_as_country_location = Country.my_objects.get(id=1)

        form_bulk.instance.user = request.user.account_profile
        form_bulk.instance.country = nigeria_as_country_location
        newly_saved_form = form_bulk.save()
        messages.success(request, "We're still preparing your customers, refresh again after some seconds.")
        newly_saved_form_id = newly_saved_form.id

        user_profile_id = request.user.account_profile.id

        # Fuction that processes our csv and creates customers
        # create_new_customers.delay(newly_saved_form_id, user_profile_id)
        create_new_customers(newly_saved_form_id, user_profile_id)

    context = {
        'form_bulk': form_bulk,
    }
    return render(request, 'platform_admin/market-sector-upload.html', context)




########################### Beginning of Market Data List View With Search ######################################
@login_required
def market_sector_data_list_view(request):
    geo_politicals = GeoPoliticalZone.my_objects.all().order_by('name')
    states = State.my_objects.all().order_by('name')
    market_sectors, search = _search_market_sector_data(request)
    categories = MarketSectorCategory.my_objects.all()
    sub_categories = MarketSectorSubCategory.my_objects.all()
    context = {
        'geo_politicals': geo_politicals,
        'states' : states,
        'categories': categories,
        'sub_categories': sub_categories,
        # 'market_sectors': market_sectors,
    }
    return render(request, 'platform_admin/market_sector/market_sector-data-list-view.html', context)


def list_search_market_sector_data_view(request):
    market_sectors, search = _search_market_sector_data(request)
    context = {"market_sectors": market_sectors, "search": search}
    return render(request, "platform_admin/market_sector/partials/search-all-market-sectors.html", context)

def _search_market_sector_data(request):
    search = request.GET.get("search")
    page = request.GET.get("page")
    market_sectors = MarketSector.my_objects.all().order_by('-id')
    
    if search:
        # orders = orders.filter(city__name__icontains=search)
        market_sectors = market_sectors.filter(description__icontains=search)

    paginator = Paginator(market_sectors, 20)
    try:
        market_sectors = paginator.page(page)
    except PageNotAnInteger:
        market_sectors = paginator.page(1)
    except EmptyPage:
        market_sectors = paginator.page(paginator.num_pages)

    return market_sectors, search or ""


########################### End of Market Data List View With Search ######################################


###################################### BEGINNING OF LOGGED IN USER MARKET_SECTOR DATA ###########################################
@login_required
def user_market_sector_list_view(request):
    user_market_sectors = _load_user_market_sectors(request)
    # objects = MarketSector.my_objects.all().order_by('-date_created')
    context = {
        'user_market_sectors': user_market_sectors,
    }
    return render(request, 'platform_admin/market_sector/user-market-sectors.html', context)


@login_required
def list_load_user_market_sectors_view(request):
    user_market_sector = _load_user_market_sectors(request)
    context = {"user_market_sectors": user_market_sector,}
    return render(request, "platform_admin/market_sector/partials/user_market_sectors.html", context)

def _load_user_market_sectors(request):
    page = request.GET.get("page")
    user = request.user.account_profile
    user_market_sectors = MarketSector.my_objects.filter(user=user).order_by('-date_created')
    paginator = Paginator(user_market_sectors, 20)
    try:
        user_market_sectors = paginator.page(page)
    except PageNotAnInteger:
        user_market_sectors = paginator.page(1)
    except EmptyPage:
        user_market_sectors = paginator.page(paginator.num_pages)
    return user_market_sectors

###################################### END OF LOGGED IN USER MARKET_SECTOR DATA ###########################################

###################################### BEGINNING OF GEOPOLITICAL ZONES FOR MARKET_SECTOR DATA ###########################################
@login_required
def market_sector_geo_zone_detail_view(request, geozone_pk):
    object = GeoPoliticalZone.my_objects.get(id=geozone_pk)
    geozone_pk = geozone_pk
    objects = _load_market_sector_geo_zone_details(request, geozone_pk)
    context = {
        'object': object,
        'objects': objects,
        'states': State.my_objects.filter(geo_political_zone=object).order_by('name'),
    }
    return render(request, 'platform_admin/market_sector/market_sector-geo-zone-detail.html', context)



@login_required
def list_load_market_sector_geo_zone_details_view(request, geozone_pk):
    object = GeoPoliticalZone.my_objects.get(id=geozone_pk)
    market_sector_geo_zone_detail = _load_market_sector_geo_zone_details(request, geozone_pk)
    context = {"objects": market_sector_geo_zone_detail, 'object': object}
    return render(request, "platform_admin/market_sector/partials/market_sector_geo_zone_details.html", context)



@login_required
def _load_market_sector_geo_zone_details(request, geozone_pk):
    page = request.GET.get("page")
    market_sector_geo_zone_details = MarketSector.my_objects.filter(geo_political_zone=geozone_pk).order_by('-date_created')
    paginator = Paginator(market_sector_geo_zone_details, 20)
    try:
        market_sector_geo_zone_details = paginator.page(page)
    except PageNotAnInteger:
        market_sector_geo_zone_details = paginator.page(1)
    except EmptyPage:
        market_sector_geo_zone_details = paginator.page(paginator.num_pages)
    return market_sector_geo_zone_details

###################################### END OF GEOPOLITICAL ZONES FOR MARKET_SECTOR DATA ###########################################



###################################### BEGINNING OF STATES LOCATION FOR MARKET_SECTOR DATA ###########################################


@login_required
def market_sector_state_location_detail_view(request, state_location_pk):
    object = State.my_objects.get(id=state_location_pk)
    state_location_pk = state_location_pk
    objects = _load_market_sector_state_location_details(request, state_location_pk)
    context = {
        'object': object,
        'objects': objects,
        'cities': City.my_objects.filter(state=object).order_by('name'),
    }
    return render(request, 'platform_admin/market_sector/market_sector-state-location-detail.html', context)



@login_required
def list_load_market_sector_state_location_details_view(request, state_location_pk):
    object = State.my_objects.get(id=state_location_pk)
    market_sector_state_location_detail = _load_market_sector_state_location_details(request, state_location_pk)
    context = {"objects": market_sector_state_location_detail, 'object': object}
    return render(request, "platform_admin/market_sector/partials/market_sector_state_location_details.html", context)



@login_required
def _load_market_sector_state_location_details(request, state_location_pk):
    page = request.GET.get("page")
    market_sector_state_location_details = MarketSector.my_objects.filter(state=state_location_pk).order_by('-date_created')
    paginator = Paginator(market_sector_state_location_details, 20)
    try:
        market_sector_state_location_details = paginator.page(page)
    except PageNotAnInteger:
        market_sector_state_location_details = paginator.page(1)
    except EmptyPage:
        market_sector_state_location_details = paginator.page(paginator.num_pages)
    return market_sector_state_location_details

###################################### END OF STATES LOCATION FOR MARKET_SECTOR DATA ###########################################




###################################### BEGINNING OF CITIES LOCATION FOR MARKET_SECTOR DATA ###########################################


@login_required
def market_sector_city_location_detail_view(request, city_location_pk):
    object = City.my_objects.get(id=city_location_pk)
    city_location_pk = city_location_pk
    objects = _load_market_sector_city_location_details(request, city_location_pk)
    context = {
        'object': object,
        'objects': objects,
        'clans': Clan.my_objects.filter(city=object).order_by('name'),
    }
    return render(request, 'platform_admin/market_sector/market_sector-city-location-detail.html', context)



@login_required
def list_load_market_sector_city_location_details_view(request, city_location_pk):
    object = City.my_objects.get(id=city_location_pk)
    market_sector_city_location_detail = _load_market_sector_city_location_details(request, city_location_pk)
    context = {"objects": market_sector_city_location_detail, 'object': object}
    return render(request, "platform_admin/market_sector/partials/market_sector_city_location_details.html", context)



@login_required
def _load_market_sector_city_location_details(request, city_location_pk):
    page = request.GET.get("page")
    market_sector_city_location_details = MarketSector.my_objects.filter(city=city_location_pk).order_by('-date_created')
    paginator = Paginator(market_sector_city_location_details, 20)
    try:
        market_sector_city_location_details = paginator.page(page)
    except PageNotAnInteger:
        market_sector_city_location_details = paginator.page(1)
    except EmptyPage:
        market_sector_city_location_details = paginator.page(paginator.num_pages)
    return market_sector_city_location_details

###################################### END OF CITIES LOCATION FOR MARKET_SECTOR DATA ###########################################




###################################### BEGINNING OF CLANS LOCATION FOR MARKET_SECTOR DATA ###########################################


@login_required
def market_sector_clan_location_detail_view(request, clan_location_pk):
    object = Clan.my_objects.get(id=clan_location_pk)
    clan_location_pk = clan_location_pk
    objects = _load_market_sector_clan_location_details(request, clan_location_pk)
    context = {
        'object': object,
        'objects': objects,
    }
    return render(request, 'platform_admin/market_sector/market_sector-clan-location-detail.html', context)



@login_required
def list_load_market_sector_clan_location_details_view(request, clan_location_pk):
    object = Clan.my_objects.get(id=clan_location_pk)
    market_sector_clan_location_detail = _load_market_sector_clan_location_details(request, clan_location_pk)
    context = {"objects": market_sector_clan_location_detail, 'object': object}
    return render(request, "platform_admin/market_sector/partials/market_sector_clan_location_details.html", context)



@login_required
def _load_market_sector_clan_location_details(request, clan_location_pk):
    page = request.GET.get("page")
    market_sector_clan_location_details = MarketSector.my_objects.filter(clan=clan_location_pk).order_by('-date_created')
    paginator = Paginator(market_sector_clan_location_details, 20)
    try:
        market_sector_clan_location_details = paginator.page(page)
    except PageNotAnInteger:
        market_sector_clan_location_details = paginator.page(1)
    except EmptyPage:
        market_sector_clan_location_details = paginator.page(paginator.num_pages)
    return market_sector_clan_location_details

###################################### END OF CLANS LOCATION FOR MARKET_SECTOR DATA ###########################################


###################################### BEGINNING OF Category FOR MARKET_SECTOR DATA ###########################################
@login_required
def market_sector_category_detail_view(request, category_pk):
    object = MarketSectorCategory.my_objects.get(id=category_pk)
    category_pk = category_pk
    objects = _load_market_sector_category_details(request, category_pk)
    context = {
        'object': object,
        'sub_categories': MarketSectorSubCategory.my_objects.filter(category=object).order_by('name'),
        'objects': objects,
        # 'market_sectors': Account.objects.all()
    }
    return render(request, 'platform_admin/market_sector/market_sector-category-detail.html', context)


@login_required
def list_load_market_sector_category_details_view(request, category_pk):
    object = MarketSectorCategory.my_objects.get(id=category_pk)
    market_sector_category_detail = _load_market_sector_category_details(request, category_pk)
    context = {"objects": market_sector_category_detail, 'object': object}
    return render(request, "platform_admin/market_sector/partials/market_sector_category_details.html", context)

@login_required
def _load_market_sector_category_details(request, category_pk):
    page = request.GET.get("page")
    market_sector_category_details = MarketSector.my_objects.filter(category=category_pk).order_by('-date_created')
    paginator = Paginator(market_sector_category_details, 20)
    try:
        market_sector_category_details = paginator.page(page)
    except PageNotAnInteger:
        market_sector_category_details = paginator.page(1)
    except EmptyPage:
        market_sector_category_details = paginator.page(paginator.num_pages)
    return market_sector_category_details


###################################### END OF Category FOR MARKET_SECTOR DATA ###########################################



###################################### BEGINNING OF SubCategory FOR MARKET_SECTOR DATA ###########################################
@login_required
def market_sector_subcategory_detail_view(request, subcategory_pk):
    object = MarketSectorSubCategory.my_objects.get(id=subcategory_pk)
    subcategory_pk = subcategory_pk
    objects = _load_market_sector_subcategory_details(request, subcategory_pk)
    context = {
        'object': object,
        'objects': objects,
    }
    return render(request, 'platform_admin/market_sector/market_sector-subcategory-detail.html', context)


@login_required
def list_load_market_sector_subcategory_details_view(request, subcategory_pk):
    object = MarketSectorSubCategory.my_objects.get(id=subcategory_pk)
    market_sector_subcategory_detail = _load_market_sector_subcategory_details(request, subcategory_pk)
    context = {"objects": market_sector_subcategory_detail, 'object': object}
    return render(request, "platform_admin/market_sector/partials/market_sector_subcategory_details.html", context)

@login_required
def _load_market_sector_subcategory_details(request, subcategory_pk):
    page = request.GET.get("page")
    market_sector_subcategory_details = MarketSector.my_objects.filter(sub_category=subcategory_pk).order_by('-date_created')
    paginator = Paginator(market_sector_subcategory_details, 2)
    try:
        market_sector_subcategory_details = paginator.page(page)
    except PageNotAnInteger:
        market_sector_subcategory_details = paginator.page(1)
    except EmptyPage:
        market_sector_subcategory_details = paginator.page(paginator.num_pages)
    return market_sector_subcategory_details


###################################### END OF SubCategory FOR MARKET_SECTOR DATA ###########################################