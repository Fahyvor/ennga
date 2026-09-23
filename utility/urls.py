from django.urls import path
from .views import load_clans, load_cities, load_states, load_subcategorys

app_name = "utility"


urlpatterns = [
    path('ajax/load-states/', load_states, name='ajax-load-states'),
    path('ajax/load-cities/', load_cities, name='ajax-load-cities'),
    path('ajax/load-clans/', load_clans, name='ajax-load-clans'),
    path('ajax/load-subcategorys/', load_subcategorys, name='ajax-load-subcategorys'),
]