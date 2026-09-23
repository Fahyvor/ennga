"""ennga URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Ennga API",
        default_version="v1",
        description="Ennga API Description",
        terms_of_service="https://www.ennga.com/terms/",
        contact=openapi.Contact(email="info@ennga.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('ckeditor/', include('ckeditor_uploader.urls')),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('', include('public.urls', namespace='public')),
    
    path('api/v1/public/',include('public.api.urls', namespace='public-api') ),
    
    path('dashboard/', include('platform_admin.urls', namespace='platform_admin')),
    path('utility/', include('utility.urls', namespace='utility')),


    path('api/v1/auth/api-auth/', include('rest_framework.urls')),
    path('api/v1/auth/rest-auth/', include('rest_auth.urls')),
    path('api/v1/auth/rest-auth/registration/', include('rest_auth.registration.urls')),
    path('api/v1/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('api/v1/auth/', include('accounts.api.urls', namespace="accounts_api")), #

    path('api/v1/utility/', include('utility.api.urls', namespace="utility_api")),
    path('api/v1/platform-admin/', include('platform_admin.api.urls', namespace="platform_admin_api")),
    path("api/v1/search-data/", include("search_data.urls", namespace="search_data_api")),
    # APIs Documentation
    path("api/docs/v1/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
]

from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

