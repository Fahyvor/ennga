from django.urls import path
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView

from .views import dashboard, edit_account_view, UpdatePassword, ProfileDetailView, profile_market_sector_view, profile_load_market_sectors_view, all_users, approved_users, admin_users
from .views_clan_access import (
    clan_access_list_view,
    grant_clan_access_view,
    revoke_clan_access_view,
    grant_subclan_access_view,
    revoke_subclan_access_view,
    api_load_subclans_for_clan_view,
    api_generate_node_id_view,
)
from .views_clans import (
    clan_list_view,
    clan_detail_view,
    clan_create_view,
    clan_edit_view,
    clan_delete_view,
    subclan_create_for_clan_view,
    subclan_create_general_view,
    subclan_edit_view,
    subclan_delete_view,
    clan_grant_access_view,
    clan_revoke_access_view,
)
from .views_market_sector import (
    market_sector_data_list_view, list_search_market_sector_data_view, market_sector_geo_zone_detail_view, list_load_market_sector_geo_zone_details_view, 
    market_sector_state_location_detail_view, list_load_market_sector_state_location_details_view, 
    market_sector_city_location_detail_view,
    list_load_market_sector_city_location_details_view, market_sector_clan_location_detail_view, list_load_market_sector_clan_location_details_view,
    market_sector_detail_view, market_sector_delete_data, user_market_sector_list_view, list_load_user_market_sectors_view, 
    market_sector_category_detail_view, list_load_market_sector_category_details_view, market_sector_subcategory_detail_view,
    list_load_market_sector_subcategory_details_view
)


from .views_historical import (historical_list_view,
    list_load_historicals_view,
    historical_data_list_view, historical_geo_zone_detail_view, list_load_historical_geo_zone_details_view, 
    historical_state_location_detail_view, list_load_historical_state_location_details_view, 
    historical_city_location_detail_view,
    list_load_historical_city_location_details_view, historical_clan_location_detail_view, list_load_historical_clan_location_details_view,
    historical_detail_view, historical_create_view, user_historical_list_view, list_load_user_historicals_view, historical_geo_political_zone_create_view, historical_state_create_view,
    historical_city_create_view, historical_clan_create_view, historical_category_detail_view, list_load_historical_category_details_view, 
    list_search_historical_data_view, historical_delete_data
)

from .views_geo_physical import (
    geo_physical_detail_view, geo_physical_list_view, list_load_geo_physicals_view, geo_physical_create_view, geo_physical_data_list_view,
    user_geo_physical_list_view, list_load_user_geo_physicals_view, geo_physical_geo_zone_detail_view,
    list_load_geo_physical_geo_zone_details_view, geo_physical_state_location_detail_view, list_load_geo_physical_state_location_details_view,
    geo_physical_city_location_detail_view, list_load_geo_physical_city_location_details_view,
    geo_physical_clan_location_detail_view, list_load_geo_physical_clan_location_details_view, geo_physical_geo_political_zone_create_view,
    geo_physical_state_create_view, geo_physical_city_create_view, geo_physical_clan_create_view,
    geo_physical_category_detail_view, list_load_geo_physical_category_details_view, list_search_geo_physical_data_view,
    geo_physical_delete_data
)

from .views import dashboard, edit_account_view, UpdatePassword, ProfileDetailView, profile_market_sector_view, profile_load_market_sectors_view, all_users, approved_users, admin_users
from .views_market_sector import (market_sector_list_view, market_sector_create_view, 
                                  list_load_market_sectors_view, market_sector_upload_view,
                                  market_sector_geo_political_zone_create_view, market_sector_state_create_view, market_sector_city_create_view, market_sector_clan_create_view
)


app_name = "platform_admin"

urlpatterns = [
    path('', dashboard, name='dashboard-root'),
    path('home/', dashboard, name='dashboard'),
    path('all-users/', all_users, name='all-users'),
    path('approved-users/', approved_users, name='approved-users'),
    path('admin-users/', admin_users, name='admin-users'),
    path('clan-access/', clan_access_list_view, name='clan-access-management'),
    path('clan-access/grant/', grant_clan_access_view, name='grant-clan-access'),
    path('clan-access/revoke/<int:clan_id>/<int:profile_id>/', revoke_clan_access_view, name='revoke-clan-access'),
    path('subclan-access/grant/', grant_subclan_access_view, name='grant-subclan-access'),
    path('subclan-access/revoke/<int:subclan_id>/<int:profile_id>/', revoke_subclan_access_view, name='revoke-subclan-access'),
    path('api/load-subclans/', api_load_subclans_for_clan_view, name='api-load-subclans'),
    path('api/generate-node-id/', api_generate_node_id_view, name='api-generate-node-id'),

    # Clans Directory & Management
    path('clans/', clan_list_view, name='clan-list'),
    path('clans/create/', clan_create_view, name='clan-create'),
    path('clans/<int:pk>/', clan_detail_view, name='clan-detail'),
    path('clans/<int:pk>/edit/', clan_edit_view, name='clan-edit'),
    path('clans/<int:pk>/delete/', clan_delete_view, name='clan-delete'),
    path('clans/<int:pk>/grant-access/', clan_grant_access_view, name='clan-grant-access'),
    path('clans/<int:pk>/revoke-access/<int:profile_id>/', clan_revoke_access_view, name='clan-revoke-access'),
    path('clans/<int:clan_id>/subclans/create/', subclan_create_for_clan_view, name='subclan-create-for-clan'),
    path('subclans/create/', subclan_create_general_view, name='subclan-create'),
    path('subclans/<int:pk>/edit/', subclan_edit_view, name='subclan-edit'),
    path('subclans/<int:pk>/delete/', subclan_delete_view, name='subclan-delete'),

    path('<user_id>/edit/', edit_account_view, name='edit-account'),
    path('change-password/', UpdatePassword.as_view(), name="update_password"),
    
    path('<int:pk>/', ProfileDetailView.as_view(), name='user-profile-view'),
    path('<int:pk>/market-sector/', profile_market_sector_view, name='user-market-sector-view'),
    path('<int:pk>/market-sector/load/', profile_load_market_sectors_view, name='profile_market_sectors'),





    #""" Beginning of hISTORIC DATA """
    path('historical/create/', historical_create_view, name="historical-create-view"),
    path('historical-geo-political-zone/<int:geozone_pk>/create/', historical_geo_political_zone_create_view, name="historical-geo-political-zone-create-view"),
    path('historical-state/<int:state_location_pk>/create/', historical_state_create_view, name="historical-state-create-view"),
    path('historical-city/<int:city_location_pk>/create/', historical_city_create_view, name="historical-city-create-view"),
    path('historical-clan/<int:clan_location_pk>/create/', historical_clan_create_view, name="historical-clan-create-view"),
    path('historical/', historical_list_view, name="historical-list-view"), # Lists all the data in market sectors
    path('historical/load/', list_load_historicals_view, name='historicals'),
    path('historical-data-list/', historical_data_list_view, name='historical-data-list-view'),
    path('historical/list-search-historical-data-view/', list_search_historical_data_view, name='list-search-historical-data-view'),
    path('historical-detail/<int:pk>/', historical_detail_view, name='historical-detail-view'),
    path('historical-delete-data/<int:pk>/', historical_delete_data, name='historical-delete-data-view'),


    ###################################### BEGINNING OF LOGGED IN USER HISTORICAL DATA ###########################################
    path('historical/user/', user_historical_list_view, name="user-historical-list-view"), # Lists all the data in market sectors
    path('historical/load/user/', list_load_user_historicals_view, name='user_historicals'),
    ###################################### END OF LOGGED IN USER HISTORICAL DATA ###########################################


    ###################################### BEGINNING OF GEOPOLITICAL ZONES FOR HISTORICAL DATA ###########################################
    path('historical-geo-zone-detail-view/<int:geozone_pk>/', historical_geo_zone_detail_view, name='historical-geo-zone-detail-view'),
    path('historical-geo-zone-detail-view/<int:geozone_pk>/load/', list_load_historical_geo_zone_details_view, name='list-load-historical-geo-zone-details-view'),

    ###################################### END OF GEOPOLITICAL ZONES FOR HISTORICAL DATA ###########################################
    

    ###################################### BEGINNING OF STATES LOCATION FOR HISTORICAL DATA ###########################################

    path('historical-state-location-detail-view/<int:state_location_pk>/', historical_state_location_detail_view, name='historical-state-location-detail-view'),
    path('historical-state-location-detail-view/<int:state_location_pk>/load/', list_load_historical_state_location_details_view, name='list-load-historical-state-location-details-view'),

    ###################################### END OF STATES LOCATION FOR HISTORICAL DATA ###########################################
    

    ###################################### BEGINNING OF CITIES LOCATION FOR HISTORICAL DATA ###########################################

    path('historical-city-location-detail-view/<int:city_location_pk>/', historical_city_location_detail_view, name='historical-city-location-detail-view'),
    path('historical-city-location-detail-view/<int:city_location_pk>/load/', list_load_historical_city_location_details_view, name='list-load-historical-city-location-details-view'),

    ###################################### END OF CITIES LOCATION FOR HISTORICAL DATA ###########################################
    

    ###################################### BEGINNING OF CLANS LOCATION FOR HISTORICAL DATA ###########################################

    path('historical-clan-location-detail-view/<int:clan_location_pk>/', historical_clan_location_detail_view, name='historical-clan-location-detail-view'),
    path('historical-clan-location-detail-view/<int:clan_location_pk>/load/', list_load_historical_clan_location_details_view, name='list-load-historical-clan-location-details-view'),

    ###################################### END OF CLANS LOCATION FOR HISTORICAL DATA ###########################################

    ###################################### BEGINNING OF CATEGORIES FOR MARKET_SECTOR DATA ###########################################
    path('historical-category-detail-view/<int:category_pk>/', historical_category_detail_view, name='historical-category-detail-view'),
    path('historical-category-detail-view/<int:category_pk>/load/', list_load_historical_category_details_view, name='list-load-historical-category-details-view'),

    ###################################### END OF CATEGORIES FOR MarketSector DATA ###########################################


    #""" Beginning of MARKET SECTOR DATA 
    path('market-sector/create/', market_sector_create_view, name="market-sector-create-view"),
    path('market-sector-geo-political-zone/<int:geozone_pk>/create/', market_sector_geo_political_zone_create_view, name="market-sector-geo-political-zone-create-view"),
    path('market-sector-state/<int:state_location_pk>/create/', market_sector_state_create_view, name="market-sector-state-create-view"),
    path('market-sector-city/<int:city_location_pk>/create/', market_sector_city_create_view, name="market-sector-city-create-view"),
    path('market-sector-clan/<int:clan_location_pk>/create/', market_sector_clan_create_view, name="market-sector-clan-create-view"),
    path('market-sector/upload/', market_sector_upload_view, name="market-sector-upload-view"),
    path('market-sector/', market_sector_list_view, name="market-sector-list-view"), # Lists all the data in market sectors
    path('market-sector/load/', list_load_market_sectors_view, name='market_sectors'),
    path('market-sector-data-list/', market_sector_data_list_view, name='market-sector-data-list-view'),
    path('market-sector/list-search-market-sector-data-view/', list_search_market_sector_data_view, name='list-search-market-sector-data-view'),
    path('market-sector-detail/<int:pk>/', market_sector_detail_view, name='market-sector-detail-view'),
    path('market-sector-delete-data/<int:pk>/', market_sector_delete_data, name='market-sector-delete-data-view'),

    
    

    ###################################### BEGINNING OF LOGGED IN USER MARKET_SECTOR DATA ###########################################
    path('market-sector/user/', user_market_sector_list_view, name="user-market-sector-list-view"), # Lists all the data in market sectors
    path('market-sector/load/user/', list_load_user_market_sectors_view, name='user_market_sectors'),
    ###################################### END OF LOGGED IN USER MARKET_SECTOR DATA ###########################################

    ###################################### BEGINNING OF GEOPOLITICAL ZONES FOR MARKET_SECTOR DATA ###########################################
    path('market-sector-geo-zone-detail-view/<int:geozone_pk>/', market_sector_geo_zone_detail_view, name='market-sector-geo-zone-detail-view'),
    path('market-sector-geo-zone-detail-view/<int:geozone_pk>/load/', list_load_market_sector_geo_zone_details_view, name='list-load-market-sector-geo-zone-details-view'),

    ###################################### END OF GEOPOLITICAL ZONES FOR MarketSector DATA ###########################################
    

    ###################################### BEGINNING OF STATES LOCATION FOR MarketSector DATA ###########################################

    path('market-sector-state-location-detail-view/<int:state_location_pk>/', market_sector_state_location_detail_view, name='market-sector-state-location-detail-view'),
    path('market-sector-state-location-detail-view/<int:state_location_pk>/load/', list_load_market_sector_state_location_details_view, name='list-load-market-sector-state-location-details-view'),

    ###################################### END OF STATES LOCATION FOR MarketSector DATA ###########################################
    

    ###################################### BEGINNING OF CITIES LOCATION FOR MarketSector DATA ###########################################

    path('market-sector-city-location-detail-view/<int:city_location_pk>/', market_sector_city_location_detail_view, name='market-sector-city-location-detail-view'),
    path('market-sector-city-location-detail-view/<int:city_location_pk>/load/', list_load_market_sector_city_location_details_view, name='list-load-market-sector-city-location-details-view'),

    ###################################### END OF CITIES LOCATION FOR MarketSector DATA ###########################################
    

    ###################################### BEGINNING OF CLANS LOCATION FOR MarketSector DATA ###########################################

    path('market-sector-clan-location-detail-view/<int:clan_location_pk>/', market_sector_clan_location_detail_view, name='market-sector-clan-location-detail-view'),
    path('market-sector-clan-location-detail-view/<int:clan_location_pk>/load/', list_load_market_sector_clan_location_details_view, name='list-load-market-sector-clan-location-details-view'),

    ###################################### END OF CLANS LOCATION FOR MarketSector DATA ###########################################

    ###################################### BEGINNING OF CATEGORIES FOR MARKET_SECTOR DATA ###########################################
    path('market-sector-category-detail-view/<int:category_pk>/', market_sector_category_detail_view, name='market-sector-category-detail-view'),
    path('market-sector-category-detail-view/<int:category_pk>/load/', list_load_market_sector_category_details_view, name='list-load-market-sector-category-details-view'),
    
    path('market-sector-subcategory-detail-view/<int:subcategory_pk>/', market_sector_subcategory_detail_view, name='market-sector-subcategory-detail-view'),
    path('market-sector-subcategory-detail-view/<int:subcategory_pk>/load/', list_load_market_sector_subcategory_details_view, name='list-load-market-sector-subcategory-details-view'),

    ###################################### END OF CATEGORIES FOR MarketSector DATA ###########################################



    #""" Beginning of MARKET SECTOR DATA 
    path('geo-physical/create/', geo_physical_create_view, name="geo-physical-create-view"),
    path('geo-physical-geo-political-zone/<int:geozone_pk>/create/', geo_physical_geo_political_zone_create_view, name="geo-physical-geo-political-zone-create-view"),
    path('geo-physical-state/<int:state_location_pk>/create/', geo_physical_state_create_view, name="geo-physical-state-create-view"),
    path('geo-physical-city/<int:city_location_pk>/create/', geo_physical_city_create_view, name="geo-physical-city-create-view"),
    path('geo-physical-clan/<int:clan_location_pk>/create/', geo_physical_clan_create_view, name="geo-physical-clan-create-view"),
    path('geo-physical/', geo_physical_list_view, name="geo-physical-list-view"), # Lists all the data in market sectors
    path('geo-physical/load/', list_load_geo_physicals_view, name='geo_physicals'),
    path('geo-physical-data-list/', geo_physical_data_list_view, name='geo-physical-data-list-view'),
    path('geo-physical/list-search-geo-physical-data-view/', list_search_geo_physical_data_view, name='list-search-geo-physical-data-view'),
    path('geo-physical-detail/<int:pk>/', geo_physical_detail_view, name='geo-physical-detail-view'),
    path('geo-physical-delete-data/<int:pk>/', geo_physical_delete_data, name='geo-physical-delete-data-view'),

    # ###################################### BEGINNING OF LOGGED IN USER GEO_PHYSICAL DATA ###########################################
    path('geo-physical/user/', user_geo_physical_list_view, name="user-geo-physical-list-view"), # Lists all the data in market sectors
    path('geo-physical/load/user/', list_load_user_geo_physicals_view, name='user_geo_physicals'),
    # ###################################### END OF LOGGED IN USER GEO_PHYSICAL DATA ###########################################

    # ###################################### BEGINNING OF GEOPOLITICAL ZONES FOR GEO_PHYSICAL DATA ###########################################
    path('geo-physical-geo-zone-detail-view/<int:geozone_pk>/', geo_physical_geo_zone_detail_view, name='geo-physical-geo-zone-detail-view'),
    path('geo-physical-geo-zone-detail-view/<int:geozone_pk>/load/', list_load_geo_physical_geo_zone_details_view, name='list-load-geo-physical-geo-zone-details-view'),

    # ###################################### END OF GEOPOLITICAL ZONES FOR GEO_PHYSICAL DATA ###########################################
    

    # ###################################### BEGINNING OF STATES LOCATION FOR GEO_PHYSICAL DATA ###########################################

    path('geo-physical-state-location-detail-view/<int:state_location_pk>/', geo_physical_state_location_detail_view, name='geo-physical-state-location-detail-view'),
    path('geo-physical-state-location-detail-view/<int:state_location_pk>/load/', list_load_geo_physical_state_location_details_view, name='list-load-geo-physical-state-location-details-view'),

    # ###################################### END OF STATES LOCATION FOR GEO_PHYSICAL DATA ###########################################
    

    # ###################################### BEGINNING OF CITIES LOCATION FOR GEO_PHYSICAL DATA ###########################################

    path('geo-physical-city-location-detail-view/<int:city_location_pk>/', geo_physical_city_location_detail_view, name='geo-physical-city-location-detail-view'),
    path('geo-physical-city-location-detail-view/<int:city_location_pk>/load/', list_load_geo_physical_city_location_details_view, name='list-load-geo-physical-city-location-details-view'),

    # ###################################### END OF CITIES LOCATION FOR GEO_PHYSICAL DATA ###########################################
    

    # ###################################### BEGINNING OF CLANS LOCATION FOR GEO_PHYSICAL DATA ###########################################

    path('geo-physical-clan-location-detail-view/<int:clan_location_pk>/', geo_physical_clan_location_detail_view, name='geo-physical-clan-location-detail-view'),
    path('geo-physical-clan-location-detail-view/<int:clan_location_pk>/load/', list_load_geo_physical_clan_location_details_view, name='list-load-geo-physical-clan-location-details-view'),

    # ###################################### END OF CLANS LOCATION FOR GEO_PHYSICAL DATA ###########################################
    
    
    ###################################### BEGINNING OF CATEGORIES FOR MARKET_SECTOR DATA ###########################################
    path('geo-physical-category-detail-view/<int:category_pk>/', geo_physical_category_detail_view, name='geo-physical-category-detail-view'),
    path('geo-physical-category-detail-view/<int:category_pk>/load/', list_load_geo_physical_category_details_view, name='list-load-geo-physical-category-details-view'),

    ###################################### END OF CATEGORIES FOR MarketSector DATA ###########################################
]
