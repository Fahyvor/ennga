from django.urls import path
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView

from .views import home, load_subclans

app_name = "account"

urlpatterns = [
     # Beginning Reset password
    path('', home, name='home'),
    path('load-subclans/', load_subclans, name='load-subclans'),
                                                                 
]
