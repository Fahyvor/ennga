from django.urls import path
from .views import (GeoPoliticalZoneListAPIView, 
                    MarketSectorDetailAPIView,
                    MarketSectorCreateAPIView,
                    MarketSectorCategoryListAPIView,
                    MarketSectorSubCategoryListAPIView
                )

app_name = "platform_admin_api"

urlpatterns = [
    path('market-sectors/geo-zone/<int:geo_political_zone_id>/', GeoPoliticalZoneListAPIView.as_view(), name='geo-zone-market-sectors'),
    path('market-sectors/detail/<int:id>/', MarketSectorDetailAPIView.as_view(), name='market-sector-detail'),
    path('market-sectors/create/', MarketSectorCreateAPIView.as_view(), name='market-sector-create'),

    path('market-sectors/categories/list/', MarketSectorCategoryListAPIView.as_view(), name='market-sector-category-list-view'),
    path('market-sectors/subcategories/list/', MarketSectorSubCategoryListAPIView.as_view(), name='market-sector-subcategory-list-view'),
]
