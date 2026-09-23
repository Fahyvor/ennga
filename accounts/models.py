from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.conf import settings
from django.contrib.auth.models import User
# from django.conf.settings import auth_user_model
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.shortcuts import reverse
from phonenumber_field.modelfields import PhoneNumberField
from utility.utils import PRIVACY_CHOICES
# from store.models import Store

# Store = store.models.Store

import os
from autoslug import AutoSlugField
from PIL import Image
from io import BytesIO


class ActiveAccountManager(BaseUserManager):
    def get_queryset(self) -> models.QuerySet:
        return super().get_queryset().filter(is_deleted=False)



class CustomAccountManager(BaseUserManager):
    def create_superuser(self, email, username, first_name, last_name, password):
        user = self.create_user(
            email = self.normalize_email(email),
            password = password,
            username = username,
            first_name = first_name,
            last_name = last_name
        )
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using = self._db)
        return user

    def create_user(self, email, username, first_name, last_name, password=None):
        if not email:
            raise ValueError("Users must have an email address")
        if not username:
            raise ValueError("Users must have a Username")

        user = self.model(
            email = self.normalize_email(email),
            username = username,
            first_name = first_name,
            last_name = last_name
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

def get_profile_image_filepath(self, filename):
    return 'profile_images/' + str(self.username) + "_" + "_" + str(self.pk) + '/profile_image.png'

def get_default_profile_image():
    return "defaultProfileImage/default.jpg"

class Account(PermissionsMixin, AbstractBaseUser):
    SEX_CHOICES = (
        ('M', 'Male',),
        ('F', 'Female',),
    )

    email = models.EmailField(verbose_name='email', max_length=50, unique=True)
    username = models.CharField(max_length=20)
    slug = AutoSlugField(populate_from='username', unique=True)

    first_name = models.CharField(max_length=20, blank=True, null=True)
    last_name = models.CharField(max_length=20, blank=True, null=True)
    sex = models.CharField(max_length=10, choices=SEX_CHOICES, blank=True, null=True)
    forgot_password_code = models.CharField(max_length=40, blank=True, null=True)
    activate_account_code = models.CharField(max_length=40, blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True,)

    profile_image = models.ImageField(max_length=255, upload_to=get_profile_image_filepath, 
                                        null=True, blank=True, default=get_default_profile_image)
    
    phone_number = PhoneNumberField(unique=True, null=False, blank=False)

    is_data_agent = models.BooleanField(default=False)
    is_editor = models.BooleanField(default=False)
    is_proof_reader = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    date_joined = models.DateTimeField(verbose_name="date joined", auto_now_add=True)
    last_login = models.DateTimeField(verbose_name="last login", auto_now=True)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    hide_email = models.BooleanField(default=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    objects = CustomAccountManager()
    actives = ActiveAccountManager()

    def __str__(self):
        return self.username

 	# To be sure of admin permissions, NOTE: all admins have permissions
    def has_perm(self, perm, obj=None):
        return self.is_admin

	# Does this user have permission to view this app? (ALWAYS YES FOR SIMPLICITY)
    def has_module_perms(self, app_label):
        return True  

    # def get_absolute_url(self):
    #     return reverse('account:account-detail-view', kwargs={'slug': self.slug, 'user_id': self.id})


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='account_profile', on_delete=models.CASCADE)
    # This is email is used for default user email address
    email = models.EmailField(verbose_name='email', max_length=50)
    bio = models.CharField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    country = models.ForeignKey("utility.Country", null=True, blank=True, on_delete=models.SET_NULL)
    state = models.ForeignKey("utility.State", null=True, blank=True, on_delete=models.SET_NULL)
    city = models.ForeignKey("utility.City", null=True, blank=True, on_delete=models.SET_NULL)
    address_location = models.CharField(max_length=255, blank=True)
    has_store = models.BooleanField(default=False)
    followers = models.ManyToManyField("Profile", blank=True, related_name='profile_followers')

    """
    This field helps to know if a user has updated their shipping 
    address so they can be shown their shipping address in basket
    """
    shipping_address_confirm = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    show_historical_data = models.BooleanField(default=False)
    show_geographical_data = models.BooleanField(default=False)
    show_market_sector_data = models.BooleanField(default=False)
    show_stored_data = models.BooleanField(default=False)
    use_analytics_tools = models.BooleanField(default=False)
    auto_analyze_data = models.BooleanField(default=False)
    public_data_uploads = models.BooleanField(default=False)

    who_can_find_me = models.CharField(
        max_length=50,
        choices=PRIVACY_CHOICES,
        blank=True,
        null=True
    )
    
    who_can_message_me = models.CharField(
        max_length=50,
        choices=PRIVACY_CHOICES,
        blank=True,
        null=True
    )
    
    who_can_share_data_with_me = models.CharField(
        max_length=50,
        choices=PRIVACY_CHOICES,
        blank=True,
        null=True
    )
    

    def __str__(self):
        return str(self.user.email)

    def get_absolute_url(self):
        return reverse('platform_admin:user-profile-view', kwargs={'pk': self.user.pk})

    def get_user_market_sector_view(self):
        return reverse('platform_admin:user-market-sector-view', kwargs={'pk': self.user.pk})
    

    def get_user_profile_url(self):
        return reverse('account:edit-user-profile-view', kwargs={'pk': self.user.pk})
        


def profile_receiver(sender, instance, created, *args, **kwargs):
    if created:
        profile = Profile.objects.create(user=instance)


post_save.connect(profile_receiver, sender=settings.AUTH_USER_MODEL)


class MobileAppForgotPasswordRequest(models.Model):
    email = models.EmailField(max_length=255)

    # This will be used to know if users entered password is correct
    forgot_password_code = models.CharField(max_length=40, blank=True, null=True)
    password = models.CharField(max_length=100, blank=True, null=True)
    confirm_password = models.CharField(max_length=100, blank=True, null=True)


    date_created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.email

class MobileAppAccountAuthenticationRequest(models.Model):
    email = models.EmailField(max_length=255)
    
    # This will be used by users to activate their accounts
    activate_account_code = models.CharField(max_length=40, blank=True, null=True)

    # This will be used to know if users entered password is correct
    forgot_password_code = models.CharField(max_length=40, blank=True, null=True)
    password = models.CharField(max_length=100, blank=True, null=True)
    confirm_password = models.CharField(max_length=100, blank=True, null=True)

    date_created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.email