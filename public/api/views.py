from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from ..models import ContactUs, FAQ
from accounts.models import Profile
from .serializers import (ContactUsSerializer, 
FAQListSerializer)


class ContactUsAPIView(generics.CreateAPIView):
    queryset = ContactUs.objects.all()
    serializer_class = ContactUsSerializer

    def post(self, request, *args, **kwargs):
        user = None
        if request.user.is_authenticated:
            user_id = request.user.id
            user = Profile.objects.get(user__id=user_id)


        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.validated_data["user"] = user
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class FAQListAPIView(generics.ListAPIView):
    queryset = FAQ.objects.all()
    serializer_class = FAQListSerializer
    pagination_class = None

class FAQDetailAPIView(generics.RetrieveAPIView):
    queryset = FAQ.objects.all()
    serializer_class = FAQListSerializer