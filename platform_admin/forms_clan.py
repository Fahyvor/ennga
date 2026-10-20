from django import forms
from utility.models import (
    Country, State, City, Clan, SubClan, GeoPoliticalZone,
    NODE_TYPE_CHOICES, ROAD_RELATION_CHOICES, ROAD_SURFACE_CHOICES, ROAD_CONDITION_CHOICES,
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
            'placeholder': 'e.g. RUM (3 letters, optional)',
            'maxlength': '10'
        })
    )
    node_id = forms.CharField(
        label='Territory Node ID',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-modern',
            'id': 'id_clan_node_id',
            'placeholder': 'e.g. CLN-001',
            'maxlength': '150',
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
        queryset=City.objects.none(),
        required=False
    )
    geo_political_zone = forms.ModelChoiceField(
        label='Geo-Political Zone (Auto-assigned from State)',
        empty_label='-- Auto-assigned from State --',
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
        if not self.instance.pk and not self.initial.get('node_id'):
            self.initial['node_id'] = Clan().generate_next_node_id()
        self.fields['geo_political_zone'].queryset = GeoPoliticalZone.objects.filter(is_deleted=False).order_by('name')
        if 'state' in self.data:
            try:
                state_id = int(self.data.get('state'))
                self.fields['city'].queryset = City.objects.filter(state_id=state_id, is_deleted=False).order_by('name')
            except (ValueError, TypeError):
                self.fields['city'].queryset = City.objects.none()
        elif self.instance.pk and self.instance.state:
            self.fields['city'].queryset = City.objects.filter(state=self.instance.state, is_deleted=False).order_by('name')
        elif self.instance.pk and self.instance.city and self.instance.city.state:
            self.fields['city'].queryset = City.objects.filter(state=self.instance.city.state, is_deleted=False).order_by('name')
        elif self.initial.get('city'):
            c_val = self.initial.get('city')
            c_id = c_val.id if hasattr(c_val, 'id') else c_val
            self.fields['city'].queryset = City.objects.filter(id=c_id)
        else:
            self.fields['city'].queryset = City.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        state = cleaned_data.get('state')
        city = cleaned_data.get('city')
        if not state and city and city.state:
            state = city.state
            cleaned_data['state'] = state
        if state and state.geo_political_zone:
            cleaned_data['geo_political_zone'] = state.geo_political_zone
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        nigeria = Country.my_objects.first() or Country.objects.first()
        if not instance.country:
            instance.country = nigeria
        if instance.city and not instance.state and instance.city.state:
            instance.state = instance.city.state
        if instance.state and instance.state.geo_political_zone:
            instance.geo_political_zone = instance.state.geo_political_zone
        elif instance.city and instance.city.state and instance.city.state.geo_political_zone:
            instance.geo_political_zone = instance.city.state.geo_political_zone
        if not instance.node_id:
            instance.node_id = instance.generate_next_node_id()
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
        queryset=Clan.objects.none(),
        required=True
    )
    node_type = forms.ChoiceField(
        label='Territorial Node Type (PRD)',
        choices=NODE_TYPE_CHOICES,
        initial='MAJOR_ROAD',
        widget=forms.Select(attrs={
            'class': 'form-control form-control-modern',
            'id': 'id_subclan_node_type'
        })
    )
    road_relation = forms.ChoiceField(
        label='Road Relationship / Alignment (for Major Roads)',
        choices=ROAD_RELATION_CHOICES,
        initial='CONTAINED_CLAN',
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control form-control-modern',
            'id': 'id_subclan_road_relation'
        })
    )
    node_id = forms.CharField(
        label='Territorial Node ID (Auto-generated)',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-modern',
            'id': 'id_subclan_node_id',
            'placeholder': 'e.g. CLN-001/SB/001 or CLN-001/SB/001/MR/001 (auto-generated)',
            'maxlength': '150',
            'readonly': 'readonly',
            'tabindex': '-1',
            'style': 'cursor: not-allowed; background-color: #f8fafc; font-family: monospace; font-weight: 600; color: #0e7490;'
        })
    )
    parent_road = forms.ModelChoiceField(
        label='Connected Major / Sub Road / Street / Sub-Clan (Territorial Parent)',
        empty_label='-- Standalone Road / Direct Trunk (No Parent) --',
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control form-control-modern',
            'id': 'id_subclan_parent_road'
        }),
        queryset=SubClan.objects.none()
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
        queryset=City.objects.none(),
        required=False
    )

    class Meta:
        model = SubClan
        fields = ('name', 'clan', 'node_type', 'road_relation', 'node_id', 'parent_road', 'road_surface', 'road_condition', 'state', 'city')
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control form-control-modern',
                'placeholder': 'Enter Road / Node Name (e.g. East-West Road, Chikwe Orlu Street, Close 2)',
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

        if clan_id:
            try:
                clan_id_int = int(clan_id)
                parent_qs = SubClan.objects.filter(clan_id=clan_id_int, is_deleted=False).only('id', 'name', 'node_type', 'node_id')
                if self.instance.pk:
                    parent_qs = parent_qs.exclude(pk=self.instance.pk)
                self.fields['parent_road'].queryset = parent_qs.order_by('name')
                self.fields['clan'].queryset = Clan.objects.filter(id=clan_id_int).only('id', 'name', 'code', 'node_id')
            except (ValueError, TypeError):
                self.fields['parent_road'].queryset = SubClan.objects.none()
                self.fields['clan'].queryset = Clan.objects.filter(is_deleted=False).only('id', 'name', 'code', 'node_id')
        else:
            state_val = self.data.get('state') or self.initial.get('state')
            if state_val:
                try:
                    s_id = int(state_val.id if hasattr(state_val, 'id') else state_val)
                    self.fields['clan'].queryset = Clan.objects.filter(
                        Q(state_id=s_id) | Q(city__state_id=s_id),
                        is_deleted=False
                    ).only('id', 'name', 'code', 'node_id').order_by('name')
                except (ValueError, TypeError):
                    self.fields['clan'].queryset = Clan.objects.filter(is_deleted=False).only('id', 'name', 'code', 'node_id')
            else:
                self.fields['clan'].queryset = Clan.objects.filter(is_deleted=False).only('id', 'name', 'code', 'node_id')
            self.fields['parent_road'].queryset = SubClan.objects.none()

        # Handle city field population
        if 'state' in self.data:
            try:
                state_id = int(self.data.get('state'))
                self.fields['city'].queryset = City.objects.filter(state_id=state_id, is_deleted=False).order_by('name')
            except (ValueError, TypeError):
                self.fields['city'].queryset = City.objects.none()
        elif self.instance.pk and self.instance.state:
            self.fields['city'].queryset = City.objects.filter(state=self.instance.state, is_deleted=False).order_by('name')
        elif self.instance.pk and self.instance.city and self.instance.city.state:
            self.fields['city'].queryset = City.objects.filter(state=self.instance.city.state, is_deleted=False).order_by('name')
        elif self.initial.get('city'):
            c_val = self.initial.get('city')
            c_id = c_val.id if hasattr(c_val, 'id') else c_val
            self.fields['city'].queryset = City.objects.filter(id=c_id)
        else:
            self.fields['city'].queryset = City.objects.none()

        # Allow valid parent_road if submitted in POST
        if 'parent_road' in self.data and self.data.get('parent_road'):
            try:
                pr_id = int(self.data.get('parent_road'))
                self.fields['parent_road'].queryset = SubClan.objects.filter(id=pr_id).only('id', 'name', 'node_type', 'node_id')
            except (ValueError, TypeError):
                pass

        self.fields['parent_road'].label_from_instance = lambda obj: f"[{obj.display_node_id}] {obj.name} ({obj.get_node_type_display()})"

    def clean(self):
        cleaned_data = super().clean()
        node_type = cleaned_data.get('node_type')
        clan = cleaned_data.get('clan')
        parent_road = cleaned_data.get('parent_road')
        road_relation = cleaned_data.get('road_relation') or 'CONTAINED_CLAN'

        # Architectural rules:
        # 1. SUB_CLAN / COMMUNITY must belong to a Clan and cannot have a parent road
        if node_type in ('SUB_CLAN', 'COMMUNITY'):
            if not clan:
                self.add_error('clan', 'Sub-clans and Communities must belong to a Clan.')
            if parent_road:
                cleaned_data['parent_road'] = None

        # 2. MAJOR_ROAD can be contained in or pass through Clan or Sub-Clan
        elif node_type == 'MAJOR_ROAD':
            if road_relation in ('CONTAINED_CLAN', 'PASSING_CLAN'):
                cleaned_data['parent_road'] = None
                if not clan:
                    self.add_error('clan', 'Major Roads must belong to a Clan.')
            elif road_relation in ('CONTAINED_SUBCLAN', 'PASSING_SUBCLAN'):
                if parent_road:
                    if parent_road.node_type not in ('SUB_CLAN', 'COMMUNITY'):
                        self.add_error('parent_road', 'For Sub-Clan alignment, the parent node must be a Sub-Clan / Community.')
                    elif not clan and parent_road.clan:
                        cleaned_data['clan'] = parent_road.clan
                elif not clan:
                    self.add_error('clan', 'Major Roads must belong to either a Clan or a Sub-Clan.')

        # 3. SUB_ROAD must belong to a Major Road
        elif node_type == 'SUB_ROAD':
            if not parent_road:
                self.add_error('parent_road', 'Sub Roads must have a parent Major Road.')
            elif parent_road.node_type not in ('MAJOR_ROAD', 'META_ROAD'):
                self.add_error('parent_road', f'Sub Roads must belong to a Major Road (selected parent is {parent_road.get_node_type_display()}).')
            elif not clan and parent_road.clan:
                cleaned_data['clan'] = parent_road.clan

        # 4. STREET must belong to a Sub Road
        elif node_type == 'STREET':
            if not parent_road:
                self.add_error('parent_road', 'Streets must have a parent Sub Road.')
            elif parent_road.node_type not in ('SUB_ROAD', 'LINK_ROAD'):
                self.add_error('parent_road', f'Streets must belong to a Sub Road (selected parent is {parent_road.get_node_type_display()}).')
            elif not clan and parent_road.clan:
                cleaned_data['clan'] = parent_road.clan

        # 5. CLOSE must belong to a Street
        elif node_type == 'CLOSE':
            if not parent_road:
                self.add_error('parent_road', 'Closes must have a parent Street.')
            elif parent_road.node_type != 'STREET':
                self.add_error('parent_road', f'Closes must belong to a Street (selected parent is {parent_road.get_node_type_display()}).')
            elif not clan and parent_road.clan:
                cleaned_data['clan'] = parent_road.clan

        return cleaned_data

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
        if clan and clan.geo_political_zone:
            instance.geo_political_zone = clan.geo_political_zone
        elif not instance.geo_political_zone and instance.state and instance.state.geo_political_zone:
            instance.geo_political_zone = instance.state.geo_political_zone
        if not instance.node_id:
            instance.node_id = instance.generate_next_node_id()
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

