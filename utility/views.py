from django.shortcuts import render

from .models import Country, State, City, Clan
from platform_admin.models import MarketSectorSubCategory
                        

def load_states(request):
    geo_political_zone_id = request.GET.get('geo_political_zone')
    states = State.my_objects.filter(geo_political_zone_id=geo_political_zone_id).order_by('name')
    return render(request, 'utility/state_dropdown_list_options.html', {'states': states})
                        

def load_cities(request):
    state_id = request.GET.get('state') or request.GET.get('state_id')
    clan_id = request.GET.get('clan') or request.GET.get('clan_id')
    state = None
    if state_id:
        try:
            state = State.objects.filter(id=int(state_id)).first()
        except (ValueError, TypeError):
            state = State.objects.filter(name__iexact=str(state_id).strip()).first()
    elif clan_id:
        try:
            clan = Clan.objects.filter(id=int(clan_id)).first()
            if clan:
                state = clan.state or (clan.city.state if clan.city else None)
        except (ValueError, TypeError):
            pass
    cities = City.my_objects.filter(state=state).order_by('name') if state else City.objects.none()
    return render(request, 'utility/city_dropdown_list_options.html', {'cities': cities, 'state': state})


from django.db.models import Q


def load_clans(request):
    city_id = request.GET.get('city') or request.GET.get('city_id')
    state_id = request.GET.get('state') or request.GET.get('state_id')
    if city_id:
        clans = Clan.my_objects.filter(city_id=city_id).order_by('name')
    elif state_id:
        from utility.territory_codes import resolve_state
        st_obj = resolve_state(state_id)
        if st_obj:
            clans = Clan.my_objects.filter(Q(state_id=st_obj.id) | Q(city__state_id=st_obj.id)).distinct().order_by('name')
        else:
            clans = Clan.my_objects.none()
    else:
        clans = Clan.my_objects.all().order_by('name')
    return render(request, 'utility/clan_dropdown_list_options.html', {'clans': clans})


def load_subcategorys(request):
    category_id = request.GET.get('category')
    subcategorys = MarketSectorSubCategory.my_objects.filter(category_id=category_id).order_by('name')
    return render(request, 'utility/subcategory_dropdown_list_options.html', {'subcategorys': subcategorys})
