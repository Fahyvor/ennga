from django import forms
from utility.models import (
    Country, State, City, Clan, SubClan, GeoPoliticalZone,
    NODE_TYPE_CHOICES, ROAD_SURFACE_CHOICES, ROAD_CONDITION_CHOICES,
    INFRASTRUCTURE_TYPE_CHOICES, INFRASTRUCTURE_STATUS_CHOICES, SIDE_OF_ROAD_CHOICES,
    TerritorialInfrastructure
)


class ClanForm(forms.ModelForm):
    code = forms.CharField(
        label='Territory Code (optional)',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-modern',
            'id': 'id_clan_code',
            'placeholder': 'e.g. RUM (3 letters, auto-derived if blank)',
            'maxlength': '10'
        })
    )
    node_id = forms.CharField(
        label='Territorial Node ID (optional)',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-modern',
            'id': 'id_clan_node_id',
            'placeholder': 'PRD pattern: e.g. RUM-CLN-001 (auto-generated if blank)',
            'maxlength': '50'
        })
    )
    state = forms.ModelChoiceField(
        label='State Location (optional)',
        empty_label='-- Select State (optional) --',
        widget=forms.Select(attrs={
            'class': 'form-control form-control-modern',
            'id': 'id_clan_state'
        }),
        queryset=State.objects.filter(is_deleted=False).order_by('name'),
        required=False
    )
    city = forms.ModelChoiceField(
        label='City / LGA Location (optional)',
        empty_label='-- Select City / LGA (optional) --',
        widget=forms.Select(attrs={
            'class': 'form-control form-control-modern',
            'id': 'id_clan_city'
        }),
        queryset=City.objects.filter(is_deleted=False).order_by('name'),
        required=False
    )
    geo_political_zone = forms.ModelChoiceField(
        label='Geo-Political Zone (optional)',
        empty_label='-- Select Zone (optional) --',
        widget=forms.Select(attrs={
            'class': 'form-control form-control-modern',
            'id': 'id_clan_geo_zone'
        }),
        queryset=GeoPoliticalZone.objects.filter(is_deleted=False).order_by('name'),
        required=False
    )

    class Meta:
        model = Clan
        fields = ('name', 'code', 'node_id', 'state', 'city', 'geo_political_zone')
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control form-control-modern',
                'placeholder': 'Enter Clan Name (e.g. Rumuigbo Clan)',
                'required': 'required'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['geo_political_zone'].queryset = GeoPoliticalZone.objects.filter(is_deleted=False).order_by('name')
        if 'state' in self.data:
            try:
                state_id = int(self.data.get('state'))
                self.fields['city'].queryset = City.objects.filter(state_id=state_id, is_deleted=False).order_by('name')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.state:
            self.fields['city'].queryset = City.objects.filter(state=self.instance.state, is_deleted=False).order_by('name')
        elif self.instance.pk and self.instance.city and self.instance.city.state:
            self.fields['city'].queryset = City.objects.filter(state=self.instance.city.state, is_deleted=False).order_by('name')

    def save(self, commit=True):
        instance = super().save(commit=False)
        nigeria = Country.my_objects.first() or Country.objects.first()
        if not instance.country:
            instance.country = nigeria
        if instance.city and not instance.state and instance.city.state:
            instance.state = instance.city.state
        if instance.state and not instance.geo_political_zone and instance.state.geo_political_zone:
            instance.geo_political_zone = instance.state.geo_political_zone
        elif instance.city and instance.city.state and not instance.geo_political_zone and instance.city.state.geo_political_zone:
            instance.geo_political_zone = instance.city.state.geo_political_zone
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class SubClanForm(forms.ModelForm):
    clan = forms.ModelChoiceField(
        label='Parent Clan',
        widget=forms.Select(attrs={
            'class': 'form-control form-control-modern',
            'id': 'id_subclan_clan'
        }),
        queryset=Clan.objects.filter(is_deleted=False).order_by('name'),
        required=True
    )
    node_type = forms.ChoiceField(
        label='Territorial Node Type (PRD)',
        choices=NODE_TYPE_CHOICES,
        initial='STREET',
        widget=forms.Select(attrs={
            'class': 'form-control form-control-modern',
            'id': 'id_subclan_node_type'
        })
    )
    node_id = forms.CharField(
        label='PRD Node ID (optional)',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-modern',
            'id': 'id_subclan_node_id',
            'placeholder': 'e.g. RUM-ST-001 (auto-generated by PRD convention if blank)',
            'maxlength': '50'
        })
    )
    parent_road = forms.ModelChoiceField(
        label='Connected Major / Link Road (Territorial Parent)',
        empty_label='-- Standalone Road / Direct Trunk --',
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control form-control-modern',
            'id': 'id_subclan_parent_road'
        }),
        queryset=SubClan.objects.filter(is_deleted=False).order_by('name')
    )
    road_surface = forms.ChoiceField(
        label='Road Surface Type',
        choices=ROAD_SURFACE_CHOICES,
        initial='ASPHALT',
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control form-control-modern',
            'id': 'id_subclan_road_surface'
        })
    )
    road_condition = forms.ChoiceField(
        label='Road Condition Assessment',
        choices=ROAD_CONDITION_CHOICES,
        initial='GOOD',
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control form-control-modern',
            'id': 'id_subclan_road_condition'
        })
    )
    state = forms.ModelChoiceField(
        label='State Location (optional)',
        empty_label='-- Select State (optional) --',
        widget=forms.Select(attrs={
            'class': 'form-control form-control-modern',
            'id': 'id_subclan_state'
        }),
        queryset=State.objects.filter(is_deleted=False).order_by('name'),
        required=False
    )
    city = forms.ModelChoiceField(
        label='City / LGA Location (optional)',
        empty_label='-- Select City / LGA (optional) --',
        widget=forms.Select(attrs={
            'class': 'form-control form-control-modern',
            'id': 'id_subclan_city'
        }),
        queryset=City.objects.filter(is_deleted=False).order_by('name'),
        required=False
    )

    class Meta:
        model = SubClan
        fields = ('name', 'clan', 'node_type', 'node_id', 'parent_road', 'road_surface', 'road_condition', 'state', 'city')
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control form-control-modern',
                'placeholder': 'Enter Node Name (e.g. Chikwe Orlu Street, Close 2)',
                'required': 'required'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Narrow parent_road options to the same clan if clan is known
        clan_id = None
        if 'clan' in self.data:
            clan_id = self.data.get('clan')
        elif self.initial.get('clan'):
            clan_val = self.initial.get('clan')
            clan_id = clan_val.id if hasattr(clan_val, 'id') else clan_val
        elif self.instance.pk and self.instance.clan:
            clan_id = self.instance.clan.id

        parent_qs = SubClan.objects.filter(is_deleted=False)
        if clan_id:
            parent_qs = parent_qs.filter(clan_id=clan_id)
        if self.instance.pk:
            parent_qs = parent_qs.exclude(pk=self.instance.pk)
        self.fields['parent_road'].queryset = parent_qs.order_by('name')

    def save(self, commit=True):
        instance = super().save(commit=False)
        clan = instance.clan
        nigeria = Country.my_objects.first() or Country.objects.first()
        if not instance.country:
            instance.country = clan.country if (clan and clan.country) else nigeria
        if not instance.state and clan and clan.state:
            instance.state = clan.state
        if not instance.city and clan and clan.city:
            instance.city = clan.city
        if not instance.geo_political_zone and clan and clan.geo_political_zone:
            instance.geo_political_zone = clan.geo_political_zone
        elif not instance.geo_political_zone and instance.state and instance.state.geo_political_zone:
            instance.geo_political_zone = instance.state.geo_political_zone
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class TerritorialInfrastructureForm(forms.ModelForm):
    clan = forms.ModelChoiceField(
        label='Parent Clan',
        widget=forms.Select(attrs={
            'class': 'form-control form-control-modern',
            'id': 'id_infra_clan'
        }),
        queryset=Clan.objects.filter(is_deleted=False).order_by('name'),
        required=True
    )
    subclan = forms.ModelChoiceField(
        label='Specific Road / Street Location (optional)',
        empty_label='-- Clan-wide / General Placement --',
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control form-control-modern',
            'id': 'id_infra_subclan'
        }),
        queryset=SubClan.objects.filter(is_deleted=False).order_by('name')
    )
    name = forms.CharField(
        label='Infrastructure Name / Title',
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-modern',
            'placeholder': 'e.g. Dual Covered Concrete Drainage - East Side, 15x Solar Streetlight Poles',
            'required': 'required'
        })
    )
    infrastructure_type = forms.ChoiceField(
        label='Infrastructure Classification',
        choices=INFRASTRUCTURE_TYPE_CHOICES,
        initial='DRAINAGE',
        widget=forms.Select(attrs={
            'class': 'form-control form-control-modern',
            'id': 'id_infra_type'
        })
    )
    status = forms.ChoiceField(
        label='Operational Status',
        choices=INFRASTRUCTURE_STATUS_CHOICES,
        initial='OPERATIONAL',
        widget=forms.Select(attrs={
            'class': 'form-control form-control-modern',
            'id': 'id_infra_status'
        })
    )
    side_of_road = forms.ChoiceField(
        label='Side of Road / Placement',
        choices=SIDE_OF_ROAD_CHOICES,
        initial='BOTH',
        widget=forms.Select(attrs={
            'class': 'form-control form-control-modern',
            'id': 'id_infra_side'
        })
    )
    quantity = forms.IntegerField(
        label='Quantity / Number of Units',
        initial=1,
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-modern',
            'placeholder': 'e.g. 1'
        })
    )
    coverage_length_meters = forms.DecimalField(
        label='Coverage / Length (Meters, optional)',
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-modern',
            'placeholder': 'e.g. 450.50'
        })
    )
    installed_by = forms.CharField(
        label='Installed / Maintained By (optional)',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-modern',
            'placeholder': 'e.g. State Ministry of Works, Community Self-Help, NDDC, Private Landlord Assn'
        })
    )
    year_installed = forms.IntegerField(
        label='Year Installed / Commissioned (optional)',
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-modern',
            'placeholder': 'e.g. 2024'
        })
    )
    gps_coordinates = forms.CharField(
        label='GPS Coordinates (Latitude, Longitude, optional)',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-modern',
            'placeholder': 'e.g. 4.8156, 7.0498'
        })
    )
    description = forms.CharField(
        label='Condition Details & Field Observations (optional)',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control form-control-modern',
            'rows': 3,
            'placeholder': 'Additional context, blockage points, damage reports, contractor info...'
        })
    )

    class Meta:
        model = TerritorialInfrastructure
        fields = (
            'clan', 'subclan', 'name', 'infrastructure_type', 'status',
            'side_of_road', 'quantity', 'coverage_length_meters',
            'installed_by', 'year_installed', 'gps_coordinates', 'description'
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        clan_id = None
        if 'clan' in self.data:
            clan_id = self.data.get('clan')
        elif self.initial.get('clan'):
            clan_val = self.initial.get('clan')
            clan_id = clan_val.id if hasattr(clan_val, 'id') else clan_val
        elif self.instance.pk and self.instance.clan:
            clan_id = self.instance.clan.id

        if clan_id:
            self.fields['subclan'].queryset = SubClan.objects.filter(clan_id=clan_id, is_deleted=False).order_by('name')

