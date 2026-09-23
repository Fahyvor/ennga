from rest_framework import serializers
from platform_admin.models import (
    MarketSector, 
    MarketSectorCategory, 
    MarketSectorSubCategory
)

from utility.api.serializers import (
    CountrySerializer,
    TribeSerializer,
    GeoPoliticalZoneSerializer,
    StateSerializer,
    CitySerializer,
    ClanSerializer,
    SubClanSerializer
)


class MarketSectorSubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketSectorSubCategory
        fields = ["id", "name"]


class MarketSectorCategorySerializer(serializers.ModelSerializer):
    subcategories = MarketSectorSubCategorySerializer(many=True, read_only=True)
    class Meta:
        model = MarketSectorCategory
        fields = ["id", "name", "is_deleted", "subcategories"]

class MarketSectorSerializer(serializers.ModelSerializer):
    country = CountrySerializer(read_only=True)
    category = MarketSectorCategorySerializer(read_only=True)
    geo_political_zone = GeoPoliticalZoneSerializer(read_only=True)
    state = StateSerializer(read_only=True)
    city = CitySerializer(read_only=True)
    clan = ClanSerializer(read_only=True)
    subclan = SubClanSerializer(read_only=True)

    class Meta:
        model = MarketSector
        fields = "__all__"


class MarketSectorCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketSector
        fields = ['category', 'sub_category', 'description', 'country', 'geo_political_zone', 'state', 'city', 'clan', 'subclan']
