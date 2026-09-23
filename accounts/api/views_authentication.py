from accounts.models import Profile, Account
from .serializers import AccountSerializer, ForgotPasswordSerializer, ProfileSerializer
from rest_framework import generics
from rest_framework.pagination import PageNumberPagination

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination

from django.contrib.auth.models import User
from accounts.models import MobileAppForgotPasswordRequest
from .serializers import RegistrationSerializer, MobileAppEnterNewPasswordSerializer
from rest_framework import generics
from accounts.tasks import send_password_reset_token_to_user

from django.http import Http404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
import random

class MobileAppForgotPasswordView(generics.CreateAPIView):
    queryset = MobileAppForgotPasswordRequest.objects.all()
    serializer_class = ForgotPasswordSerializer

    def post(self, request):
        serializer = self.serializer_class(**{'data': request.data})
        serializer.is_valid()
        # serializer.save()
        # if 
        entered_email = serializer.data['email']
        accounts = Account.objects.all()

        if Account.objects.filter(email=entered_email).exists():

            # print("Account Rhyme oh")
            user_account_id = Account.objects.get(email=entered_email)
            account_id = user_account_id.id
            _forgot_password_code = random.randint(000000,999999)
            Account.objects.filter(email=entered_email).update(forgot_password_code=_forgot_password_code)

            # Send password reset token to user
            send_password_reset_token_to_user(account_id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        else:
            # print("Account no Rhyme oh")
            # pass

            # return Response(status=status.HTTP_201_CREATED)
            raise Http404





class MobileAppEnterNewPasswordView(generics.CreateAPIView):
    queryset = MobileAppForgotPasswordRequest.objects.all()
    serializer_class = MobileAppEnterNewPasswordSerializer

    def post(self, request):
        serializer = self.serializer_class(**{'data': request.data})
        serializer.is_valid()

        
        data = request.data
        entered_forgot_password_code = serializer.data['forgot_password_code']
        entered_password = serializer.data['password']
        user = Account.objects.get(forgot_password_code=entered_forgot_password_code)


        if Account.objects.filter(forgot_password_code=entered_forgot_password_code).exists():
            if user:
                user.set_password(entered_password)
                user.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                # raise Http404
                return Response(serializer.data, status=status.HTTP_404_NOT_FOUND)
        else:
            # raise Http404
            return Response(serializer.data, status=status.HTTP_404_NOT_FOUND)