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
    SubClan
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
        fields = ["id", "name",]


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


class SubClanSerializer(serializers.ModelSerializer):
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