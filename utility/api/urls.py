from django.urls import path
from .views import (
    GeoPoliticalZoneListAPIView,
    GeoPoliticalZoneDetailAPIView,
    StatesListAPIView,
    StateDetailAPIView
)

app_name = 'utility_api'

urlpatterns = [
    path('geo-political-zone-list-api-view/', GeoPoliticalZoneListAPIView.as_view(),),
    path('geo-political-zone-detail-api-view/<int:id>/', GeoPoliticalZoneDetailAPIView.as_view(),),
    path('states-list-api-view/', StatesListAPIView.as_view(),),
    path('states-detail-api-view/<int:id>/', StateDetailAPIView.as_view(),),
]
