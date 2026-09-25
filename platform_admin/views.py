from django.shortcuts import render, redirect, reverse
from django.contrib.auth.decorators import login_required
from accounts.models import Account, Profile
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.contrib import messages

from django.contrib.auth.views import PasswordChangeView
from django.contrib.auth.forms import PasswordChangeForm
from accounts.forms import (RegistrationForm, AccountAuthenticationForm, 
                            AccountUpdateForm, UserProfileUpdateForm)
from accounts.models import Account, Profile
from django.conf import settings
from .forms import MarketSectorForm, MarketSectorBulkDataForm
from .models import MarketSectorBulkData, MarketSector, Historical, GeoPhysicalData
from .tasks import create_new_customers
from utility.models import Country, Clan, SubClan, State, City, GeoPoliticalZone, NODE_TYPE_CHOICES
from .forms_clan import ClanForm, SubClanForm
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.views.generic import ( ListView, DetailView, CreateView, 
                                    UpdateView, DeleteView, RedirectView, View, TemplateView)


@login_required
def dashboard(request):
    users = Profile.objects.all()
    market_sectors = MarketSector.my_objects.all()
    historicals = Historical.my_objects.all()
    geo_physicals = GeoPhysicalData.my_objects.all()

    profile = getattr(request.user, 'account_profile', None)
    is_admin = bool(request.user.is_admin or request.user.is_superuser or request.user.is_staff)

    assigned_clans = profile.clan_managers.filter(is_deleted=False).select_related('city', 'state') if profile else Clan.objects.none()
    assigned_subclans = profile.subclan_managers.filter(is_deleted=False).select_related('clan', 'city', 'state') if profile else SubClan.objects.none()
    
    total_clans_count = Clan.objects.filter(is_deleted=False).count()
    total_subclans_count = SubClan.objects.filter(is_deleted=False).count()

    # If admin and no explicit assignments, supply recent clans so admin has interactive access immediately
    admin_recent_clans = Clan.objects.filter(is_deleted=False).select_related('city', 'state').order_by('-id')[:8] if is_admin else Clan.objects.none()

    all_clans_dropdown = Clan.objects.filter(is_deleted=False).select_related('city', 'state').order_by('name')
    all_users = Account.objects.filter(is_active=True).select_related('account_profile').order_by('first_name', 'username')
    all_states = State.objects.filter(is_deleted=False).order_by('name')

    clan_create_form = ClanForm()
    subclan_create_form = SubClanForm()

    context = {
        'users': users,
        'historicals': historicals,
        'market_sectors': market_sectors,
        'geo_physicals': geo_physicals,
        'assigned_clans': assigned_clans,
        'assigned_subclans': assigned_subclans,
        'admin_recent_clans': admin_recent_clans,
        'total_clans_count': total_clans_count,
        'total_subclans_count': total_subclans_count,
        'is_admin': is_admin,
        'all_clans_dropdown': all_clans_dropdown,
        'all_users': all_users,
        'all_states': all_states,
        'clan_create_form': clan_create_form,
        'subclan_create_form': subclan_create_form,
        'node_type_choices': NODE_TYPE_CHOICES,
    }
    return render(request, 'platform_admin/dashboard.html', context)

@login_required
def all_users(request):
    users = Account.objects.all()
    context = {
        'users': users,
    }
    return render(request, 'platform_admin/all-users.html', context)

@login_required
def approved_users(request):
    users = Account.objects.filter(is_active=True)
    context = {
        'users': users,
    }
    return render(request, 'platform_admin/approved-users.html', context)

@login_required
def admin_users(request):
    users = Account.objects.filter(is_active=True, is_admin=True)
    context = {
        'users': users,
    }
    return render(request, 'platform_admin/admin-users.html', context)


@login_required
def edit_account_view(request, *args, **kwargs):
    user = request.user.account_profile
    market_sectors = MarketSector.my_objects.filter(user=user).order_by('-date_created')
    historicals = Historical.my_objects.filter(user=user).order_by('-date_created')
    geo_physicals = GeoPhysicalData.my_objects.filter(user=user).order_by('-date_created')

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
            messages.success(request, "Account updated successfully.")
            new_username = form.cleaned_data['username']
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            return redirect("platform_admin:edit-account", user_id=account.pk)
        else:
            form = AccountUpdateForm(request.POST, instance=request.user,
                    initial={
                        "id": account.pk,
                        "email": account.email,
                        "username": account.username,
                        "first_name": account.first_name,
                        "last_name": account.last_name,
                    })
            context['form'] = form
    else:
        form = AccountUpdateForm(
			initial={
					"id": account.pk,
					"email": account.email,
					"username": account.username,
					"first_name": account.first_name,
					"last_name": account.last_name,
				}
			)
        context['form'] = form
        context['market_sectors'] = market_sectors
        context['historicals'] = historicals
        context['geo_physicals'] = geo_physicals
        context['object'] = user
    context['DATA_UPLOAD_MAX_MEMORY_SIZE'] = settings.DATA_UPLOAD_MAX_MEMORY_SIZE
    return render(request, 'platform_admin/edit_account.html', context)




class UpdatePassword(PasswordChangeView):
    form_class = PasswordChangeForm
    # success_url = '/user/edit-profile'
    template_name = 'platform_admin/change-password.html'

    def get_success_url(self):
        return reverse('platform_admin:update_password')
    
    def form_valid(self, form):
        messages.success(self.request, "Password changed successfully.")
        return HttpResponseRedirect(self.get_success_url())


class ProfileDetailView(DetailView):
    model = Profile
    template_name = 'platform_admin/profile.html'
 
    # override context data
    def get_context_data(self, *args, **kwargs):
        profile = self.object
        context = super(ProfileDetailView, self).get_context_data(*args, **kwargs)
        context['market_sectors'] = MarketSector.my_objects.filter(user=profile)
        context['historicals'] = Historical.my_objects.filter(user=profile)
        context['geo_physicals'] = GeoPhysicalData.my_objects.filter(user=profile)
        context['assigned_clans'] = profile.clan_managers.filter(is_deleted=False).select_related('city', 'state')
        context['assigned_subclans'] = profile.subclan_managers.filter(is_deleted=False).select_related('clan')
        context['all_clans'] = Clan.objects.filter(is_deleted=False).order_by('name')
        context['all_subclans'] = SubClan.objects.filter(is_deleted=False).select_related('clan').order_by('name')
        context['is_admin'] = self.request.user.is_admin or self.request.user.is_superuser
        return context


def profile_market_sector_view(request, pk):
    user = Profile.objects.get(id=pk)
    market_sectors = _load_market_sectors(request, pk)
    user_market_sectors = MarketSector.my_objects.filter(user=user)
    context = {
        'market_sectors': market_sectors,
        'user': user,
        'user_market_sectors': user_market_sectors
    }
    return render(request, 'platform_admin/profile_market_sector.html', context)


def profile_load_market_sectors_view(request):
    market_sector = _load_market_sectors(request)
    context = {"market_sectors": market_sector,}
    return render(request, "platform_admin/partials/profile_market_sectors.html", context)


def _load_market_sectors(request, pk):
    page = request.GET.get("page")
    user = Profile.objects.get(id=pk)
    market_sectors = MarketSector.my_objects.filter(user=user).order_by('-date_created')
    paginator = Paginator(market_sectors, 50)
    try:
        market_sectors = paginator.page(page)
    except PageNotAnInteger:
        market_sectors = paginator.page(1)
    except EmptyPage:
        market_sectors = paginator.page(paginator.num_pages)
    return market_sectors