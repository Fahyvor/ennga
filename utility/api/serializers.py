import random
import string
from rest_framework import serializers
from utility.models import (
    Country,
    Tribe,
    GeoPoliticalZone,
    State,
    City,
    Clan,
    SubClan,
    TerritorialInfrastructure
)

class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = "__all__"


class TribeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tribe
        fields = "__all__"


class ClanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Clan
        fields = ["id", "name", "code", "node_id"]


class CitySerializer(serializers.ModelSerializer):
    clan_cities = ClanSerializer(many=True, read_only=True)
    class Meta:
        model = City
        fields = ["id", "name", "clan_cities"]


class StateSerializer(serializers.ModelSerializer):
    city_states = CitySerializer(many=True, read_only=True)
    class Meta:
        model = State
        fields = ["id", "name", "city_states"]


class GeoPoliticalZoneSerializer(serializers.ModelSerializer):
    state_geo_political_zones = StateSerializer(many=True, read_only=True)
    class Meta:
        model = GeoPoliticalZone
        fields = ["id", "country", "name", "state_geo_political_zones"]


class TerritorialInfrastructureSerializer(serializers.ModelSerializer):
    infrastructure_type_display = serializers.CharField(source='get_infrastructure_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    side_of_road_display = serializers.CharField(source='get_side_of_road_display', read_only=True)
    clan_name = serializers.CharField(source='clan.name', read_only=True)
    subclan_name = serializers.CharField(source='subclan.name', read_only=True)

    class Meta:
        model = TerritorialInfrastructure
        fields = "__all__"


class SubClanSerializer(serializers.ModelSerializer):
    parent_road_name = serializers.CharField(source='parent_road.name', read_only=True)
    node_type_display = serializers.CharField(source='get_node_type_display', read_only=True)
    road_surface_display = serializers.CharField(source='get_road_surface_display', read_only=True)
    road_condition_display = serializers.CharField(source='get_road_condition_display', read_only=True)
    total_infrastructures = serializers.IntegerField(read_only=True)
    infrastructures = TerritorialInfrastructureSerializer(many=True, read_only=True)

    class Meta:
        model = SubClan
        fields = "__all__"


class GeoPoliticalZoneDetailSerializer(serializers.ModelSerializer):
    country = CountrySerializer(read_only=True)
    class Meta:
        model = GeoPoliticalZone
        fields = "__all__"


class StateDetailSerializer(serializers.ModelSerializer):
    country = CountrySerializer(read_only=True)
    geo_political_zone = GeoPoliticalZoneSerializer(read_only=True)
    class Meta:
        model = State
        fields = "__all__"