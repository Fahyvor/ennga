import random

from rest_framework import permissions
from rest_framework import status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import generics

from utility.models import (
    GeoPoliticalZone,
    State,
)
from .serializers import (
    GeoPoliticalZoneSerializer,
    StateSerializer,
    GeoPoliticalZoneDetailSerializer,
    StateDetailSerializer
)


class GeoPoliticalZoneListAPIView(generics.ListAPIView):
    queryset = GeoPoliticalZone.objects.all()
    serializer_class = GeoPoliticalZoneSerializer
    permission_classes = (permissions.AllowAny,)


class GeoPoliticalZoneDetailAPIView(generics.RetrieveAPIView):
    queryset = GeoPoliticalZone.objects.all()
    serializer_class = GeoPoliticalZoneDetailSerializer
    permission_classes = (permissions.AllowAny,)
    lookup_field = 'id'


class StatesListAPIView(generics.ListAPIView):
    queryset = State.objects.all()
    serializer_class = StateSerializer
    permission_classes = (permissions.AllowAny,)


class StateDetailAPIView(generics.RetrieveAPIView):
    queryset = State.objects.all()
    serializer_class = StateDetailSerializer
    permission_classes = (permissions.AllowAny,)
    lookup_field = 'id'