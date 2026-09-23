from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.urls import reverse_lazy
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.forms.models import model_to_dict
from django.views.generic import View, CreateView, DetailView, ListView, UpdateView
from django.utils.http import is_safe_url
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.core.files.storage import default_storage
from django.core.files.storage import FileSystemStorage
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.core import files
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.http import HttpResponseRedirect, HttpResponseNotFound, Http404
from django.urls import reverse
from datetime import datetime

import random
import string
import os
# import cv2
import json
import base64
import requests

from accounts.forms import (RegistrationForm, AccountAuthenticationForm, 
                            AccountUpdateForm, UserProfileUpdateForm)
from accounts.models import Account, Profile
from .tokens import account_activation_token

from django.views.decorators.http import require_http_methods

TEMP_PROFILE_IMAGE_NAME = "temp_profile_image.png"



def register_view(request):
    
    if request.user.is_authenticated:
        return redirect("/")

    if request.method == "POST":
        form = RegistrationForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.email = form.cleaned_data["email"]
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']

            users_alphabets = (''.join(random.choices(string.ascii_lowercase, k=5)))
            users_number = random.randint(00000,99999)

            user.username = str(users_alphabets) + str(users_number)
            # user.sex = form.cleaned_data['sex']            
            user.is_active = False
            user.save()
            new_user_id = user.id
            id = new_user_id


            print("THis is just the id, lol: " + str(id))
            current_site = get_current_site(request)
            mail_subject = 'Activate your account.'
            to_email = form.cleaned_data["email"]
            
            context =  {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
            }
            html_tpl_path = 'accounts/registration/account_activation_email.html'
            email_html_template = get_template(html_tpl_path).render(context)

            email_msg = EmailMessage(
                mail_subject,
                email_html_template, 
                [settings.DEFAULT_FROM_EMAIL,], # From Email
                [to_email], # To Email
                reply_to=[settings.DEFAULT_FROM_EMAIL,]
            )
            # this is the crucial part that sends email as html content but not as a plain text
            email_msg.content_subtype = 'html'
            email_msg.send(fail_silently=False)
            # return email_msg


            print('registration successful')
            return render(request, "accounts/registration/register_email_confirm.html", {"form": form})
        else:
            return render(request, 'accounts/register.html', {"form": form, "registration_form": form})

    else:
        form = RegistrationForm()
    return render(request, 'accounts/register.html', {"form": form, "registration_form": form})


def logout_view(request):
    logout(request)
    return redirect('public:home')


# New login view that redirects and not like the old login 
# view that uses the get_redirect_f _exists
def login_view(request, *args, **kwargs):
    context = {}
    user = request.user
    if user.is_authenticated:
        return redirect("public:home")

    if request.POST:
        form = AccountAuthenticationForm(request.POST)
        if form.is_valid():
            email = request.POST['email']
            password = request.POST['password']
            user = authenticate(email=email, password=password)

            if user:
                login(request, user)
                if request.GET:
                    if request.GET.get("next"):
                        return redirect(request.GET.get('next'))
                return redirect("public:home")
    else:
        form = AccountAuthenticationForm()
    context['login_form'] = form
    return render(request, "accounts/login.html", context)


def get_redirect_if_exists(request):
    # redirect = None
    redirect = settings.LOGIN_REDIRECT_URL
    if request.GET:
        if request.GET.get("next"):
            redirect = str(request.GET.get("NEXT"))
    return redirect


@login_required
def account_view(request, *args, **kwargs):
    context = {}
    user_id = kwargs.get("user_id")
    #page = Page.objects.filter(owner=request.user.profile)#.order_by('-cr_date')
    try:
        account = Account.objects.get(pk=user_id)
        profile = Profile.objects.get(pk=user_id)
    except:
        return HttpResponse('Something went wrong.')
    
    # user_results = Result.objects.filter(user=request.user.profile)

    if request.method == "GET":
        context['account'] = account
        context['object'] = account
        context['id'] = account.id
        context['username'] = account.username
        context['first_name'] = account.first_name
        context['last_name'] = account.last_name
        context['email'] = account.email
        # context['profile_image'] = account.profile_image.url
        context['hide_email'] = account.hide_email
        context['bio'] = profile.bio
        context['profile'] = profile
        context['phone_number'] = profile.phone_number
        # context['stores'] = Store.objects.filter(owner=request.user.profile)
        # profile_image = account.profile_image.url

        # Get total user Orders
        # context["user_orders"] = Payment.objects.filter(user=request.user.profile)

        is_self = True
        friend_requests = None
        user = request.user
        if user.is_authenticated and user != account:
            is_self = False

        elif not user.is_authenticated:
            is_self = False
    
            # Set the template variables to the values
        context['is_self'] = is_self
        # context['BASE_URL'] = settings.BASE_URL
        return render(request, "accounts/account.html", context)

    
@login_required
def edit_account_view(request, *args, **kwargs):
    if not request.user.is_authenticated:
        return redirect('accounts:login')
    user_id = kwargs.get("user_id")
    account = Account.objects.get(pk=user_id)
    if account.pk != request.user.pk:
        return HttpResponse("You cannot edit someone elses profile.")
    context = {}
    if request.POST:
        form = AccountUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            #new_username = form.cleaned_data['username']
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            return redirect("accounts:user-account-view", user_id=account.pk)
        else:
            form = AccountUpdateForm(request.POST, instance=request.user,
                    initial={
                        "id": account.pk,
                        "email": account.email,
                        #"username": account.username,
                        "first_name": account.first_name,
                        "last_name": account.last_name,
                    })
            context['forom'] = form
    else:
        form = AccountUpdateForm(
			initial={
					"id": account.pk,
					"email": account.email,
					#"username": account.username,
					"first_name": account.first_name,
					"last_name": account.last_name,
				}
			)
        context['form'] = form
    context['DATA_UPLOAD_MAX_MEMORY_SIZE'] = settings.DATA_UPLOAD_MAX_MEMORY_SIZE
    return render(request, 'accounts/edit_account.html', context)


@login_required
def edit_user_profile_view(request, *args, **kwargs):
    if not request.user.is_authenticated:
        return redirect('accounts:login')
    user_id = kwargs.get('user_id')
    account = Account.objects.get(pk=user_id)
    profile = Profile.objects.get(pk=user_id)

    if account.pk != request.user.pk:
        return HttpResponse("You cannot edit someone elses profile credentials.")
    
    context = {}
    if request.POST:
        form = UserProfileUpdateForm(request.POST, instance=request.user.profile)
        account_form = AccountUpdateForm(request.POST, instance=request.user)

        if form.is_valid() and account_form.is_valid():
            form.save()
            account_form.save()
            messages.success(request, "Profile Updated Successfully")
            return redirect("accounts:user-account-view", user_id=account.pk)
        else:
            form = UserProfileUpdateForm(request.POST, instance=request.user.profile,
                initial = {
                    "id": profile.pk,
                    "phone_number": profile.phone_number,
                    "address_location": profile.address_location,
                })
            
            account_form = AccountUpdateForm(request.POST, instance=request.user,
                initial = {
                    "email": account.email,
                    "first_name": account.first_name,
                    "last_name": account.last_name,
                })

            # context['form'] = form
            # context['account_form'] = account_form
    else:
        form = UserProfileUpdateForm(
            initial={
                    "id": profile.pk,
                    "phone_number": profile.phone_number,
                    "address_location": profile.address_location,
                }
            )

        account_form = AccountUpdateForm(
                initial = {
                    "email": account.email,
                    "first_name": account.first_name,
                    "last_name": account.last_name,
                })

        context = {
            "form": form,
            "account_form": account_form
        }
    return render(request, "accounts/edit_profile.html", context)


def account_activate(request, uidb64, token):
    User = get_user_model()
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        return redirect("/")    
    else:
        return render(request, "accounts/registration/activation_invalid.html")







