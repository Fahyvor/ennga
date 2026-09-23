from rest_framework import serializers
from djoser.serializers import UserCreateSerializer
from django.contrib.auth import get_user_model
from .models import Account
# User = get_user_model()

class UserCreateSerializer(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):
        model = Account
        fields = ('id', 'email', 'first_name', 'last_name', 'password')

    def	save(self):

        account = Account(
        email=self.validated_data['email'],
        first_name = self.validated_data['first_name'],
        last_name = self.validated_data['last_name'],
        )
		
        account.save()
        return account


class UserDetailsSerializer(serializers.ModelSerializer):
    """
    User model w/o password
    """
    class Meta:
        model = Account
        fields = ('pk', 'username', 'email', 'first_name', 'last_name',)
        read_only_fields = ('email', )