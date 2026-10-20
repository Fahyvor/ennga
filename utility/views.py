from django.shortcuts import render

from .models import Country, State, City, Clan
from platform_admin.models import MarketSectorSubCategory
                        

def load_states(request):
    geo_political_zone_id = request.GET.get('geo_political_zone')
    states = State.my_objects.filter(geo_political_zone_id=geo_political_zone_id).order_by('name')
    return render(request, 'utility/state_dropdown_list_options.html', {'states': states})
                        

def load_cities(request):
    state_id = request.GET.get('state')
    state = State.objects.filter(id=state_id).first() if state_id else None
    cities = City.my_objects.filter(state_id=state_id).order_by('name') if state_id else City.objects.none()
    return render(request, 'utility/city_dropdown_list_options.html', {'cities': cities, 'state': state})


from django.db.models import Q


def load_clans(request):
    city_id = request.GET.get('city') or request.GET.get('city_id')
    state_id = request.GET.get('state') or request.GET.get('state_id')
    if city_id:
        clans = Clan.my_objects.filter(city_id=city_id).order_by('name')
    elif state_id:
        clans = Clan.my_objects.filter(Q(state_id=state_id) | Q(city__state_id=state_id)).distinct().order_by('name')
    else:
        clans = Clan.my_objects.all().order_by('name')
    return render(request, 'utility/clan_dropdown_list_options.html', {'clans': clans})


def load_subcategorys(request):
    category_id = request.GET.get('category')
    subcategorys = MarketSectorSubCategory.my_objects.filter(category_id=category_id).order_by('name')
    return render(request, 'utility/subcategory_dropdown_list_options.html', {'subcategorys': subcategorys})
