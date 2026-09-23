import random
import string
from accounts.models import Account, Profile

from django.core.validators import EmailValidator
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from djoser.serializers import UserCreateSerializer

from accounts.tasks import send_password_activate_token_to_user, send_password_reset_token_to_user
from accounts.models import Account, MobileAppAccountAuthenticationRequest
from datetime import date

class UserCreateSerializer(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):
        model = Account
        fields = ('id', 'email', 'first_name', 'phone_number', 'last_name', 'password')

    def	save(self):
        account = Account(email=self.validated_data['email'],
                        phone_number=self.validated_data['phone_number'],
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
        fields = ('pk', 'phone_number', 'email', 'first_name', 'last_name',)
        read_only_fields = ('email', )


class CustomRegistrationSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True, required=True)
    class Meta:
        model = Account
        fields = ('id', 'email', 'phone_number', 'first_name', 'last_name','password', 'password2')

        extra_kwargs = {
            "email": {
                "validators": [
                    EmailValidator,
                    UniqueValidator(
                        queryset=Account.objects.all(),
                        message="This email already exist, you can proceed to verify."
                    )
                ]
            }
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError(
            {"password": "Password fields didn't match."})
        return attrs

    
    # def validate_email(self, value):
    #     if Account.objects.filter(email=value).exists():
    #         raise serializers.ValidationError("This email already exists!.")
    #     return value


    def create(self, validated_data):
        email = validated_data['email']
        phone_number = validated_data['phone_number']
        first_name = validated_data['first_name']
        last_name = validated_data['last_name']
        users_alphabets = (''.join(random.choices(string.ascii_lowercase, k=5)))
        users_number = random.randint(00000,99999)
        username = str(users_alphabets) + str(users_number)

        _activate_account_code = random.randint(100000, 999999)
        
        
        user = Account.objects.create(
            username=username,
            email=email,
            phone_number=phone_number,
            first_name=first_name,
            last_name=last_name,
            activate_account_code=_activate_account_code,
            is_active=False,
        )

        user.set_password(validated_data['password'])
        user.save()
        new_account_id = user.id
        email = send_password_activate_token_to_user(new_account_id)
        return user
    

class ResendRegistrationOTPCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MobileAppAccountAuthenticationRequest
        fields = ['email',]


class MobileAppAccountAuthenticationRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ('id', 'activate_account_code',)


class ForgotPasswordSerializer(serializers.ModelSerializer):
	class Meta:
		model = MobileAppAccountAuthenticationRequest
		fields = ['id', 'email',]


class MobileAppEnterNewPasswordSerializer(serializers.ModelSerializer):
	class Meta:
		model = MobileAppAccountAuthenticationRequest
		fields = ['id', 'forgot_password_code', 'password', 'confirm_password']


class AccountSerializer(serializers.ModelSerializer):
    age = serializers.SerializerMethodField()
    class Meta:
        model = Account
        fields = ('id', 
                  'phone_number', 
                  'first_name', 
                  'last_name', 
                  'date_of_birth', 
                  'age', 
                  'sex', 
                  'is_active', 
                  'profile_image', 
                  'date_joined'
                )

    def get_age(self, obj):
        if obj.date_of_birth:
            today = date.today()
            age = today.year - obj.date_of_birth.year
            if today.month < obj.date_of_birth.month or (today.month == obj.date_of_birth.month and today.day < obj.date_of_birth.day):
                age -= 1
            return age
        else:
            return None


class AccountUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ('id', 'phone_number', 'first_name', 'last_name', 'email')

class AccountProfileDetailSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    email = serializers.CharField(required=False)
    
    class Meta:
        model = Account
        fields = ["id","first_name", "last_name", "email"]
 

class AccountDetailSerializer(serializers.ModelSerializer):
     class Meta:
          model = Account
          fields = ["id","first_name", "last_name", "username", "email", "phone_number","profile_image"]
class ProfileDetailSerializer(serializers.ModelSerializer):
    user = AccountProfileDetailSerializer(read_only=True)
    class Meta:
        model = Profile
        fields = [
            "id",
            "user",
            "phone_number", 
            "address_location",
            "show_historical_data", 
            "show_geographical_data", 
            "show_market_sector_data",
            "show_stored_data", 
            "use_analytics_tools", 
            "auto_analyze_data", 
            "public_data_uploads", 
            "who_can_find_me", 
            "who_can_message_me", 
            "who_can_share_data_with_me"
        ]

class ProfileDetailUpdateSerializer(serializers.ModelSerializer):
    user = AccountProfileDetailSerializer()
    class Meta:
        model = Profile
        fields = [
            "id",
            "user",
            "phone_number", 
            "address_location",
            "show_historical_data", 
            "show_geographical_data", 
            "show_market_sector_data",
            "show_stored_data", 
            "use_analytics_tools", 
            "auto_analyze_data", 
            "public_data_uploads", 
            "who_can_find_me", 
            "who_can_message_me", 
            "who_can_share_data_with_me"
        ]
        

    def update(self, instance, validated_data):
         user = validated_data.pop("user")
         Account.actives.update(**user)
         return super().update(instance, validated_data)



class AccountProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
         model = Account
         fields = ["first_name","last_name","email"]



class ProfileUpdateSerializer(serializers.ModelSerializer):
    user = AccountProfileUpdateSerializer()
    class Meta:
        model = Profile
        fields = ["user", "phone_number", "address_location"]

    def update(self, instance, validated_data):
         account_details = validated_data.pop("user")
         Account.objects.update(**account_details)
         Profile.objects.update(**validated_data)
         return instance
    

class ProfilePasswordUpdateSerializer(serializers.Serializer):
     old_password = serializers.CharField()
     new_password = serializers.CharField()
     confirm_password = serializers.CharField()


class PrivacyUpdateSerializer(serializers.ModelSerializer):
     class Meta:
          model = Profile
          fields = ["who_can_find_me", "who_can_message_me", "who_can_share_data_with_me"]
     



class PreferencesUpdateSerializer(serializers.ModelSerializer):
     class Meta:
          model = Profile
          fields = ["show_historical_data", "show_geographical_data", "show_stored_data","use_analytics_tools", "auto_analyze_data", "public_data_uploads"]




class UserAccountDeleteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ["id", "is_deleted"]