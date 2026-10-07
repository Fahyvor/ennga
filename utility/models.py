from django.db import models
from django.urls import reverse
from ckeditor_uploader.fields import RichTextUploadingField


class CountryManager(models.Manager):
    def get_queryset(self):
        return super(CountryManager, self).get_queryset().filter(is_deleted=False)
    

class Country(models.Model):
    name = models.CharField(max_length=255)
    is_deleted = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    objects = models.Manager() 
    my_objects = CountryManager()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Countries'
    

class Tribe(models.Model):
    name = models.CharField(max_length=255)
    description = RichTextUploadingField(blank=True, null=True,)
    is_deleted = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    objects = models.Manager() 
    my_objects = CountryManager()

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Tribes"

    class Meta:
        ordering = ['name',]


class GeoPoliticalZone(models.Model):
    country = models.ForeignKey(Country, null=True, on_delete=models.SET_NULL, related_name='geo_political_zone_countries')
    name = models.CharField(max_length=255)
    managers = models.ManyToManyField("accounts.Profile", blank=True, related_name='geo_political_zone_managers')
    is_deleted = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    objects = models.Manager() 
    my_objects = CountryManager()

    def __str__(self):
        return self.name
        
    class Meta:
        verbose_name_plural = 'Geo Political Zones'

    class Meta:
        ordering = ['name',]


    def get_historical_geo_zone_detail_url(self):
        return reverse('platform_admin:historical-geo-zone-detail-view', kwargs={'geozone_pk': self.pk})

    def get_list_load_historical_geo_zone_details_url(self):
        return reverse('platform_admin:list-load-historical-geo-zone-details-view', kwargs={'geozone_pk': self.pk})


    def get_market_sector_geo_zone_detail_url(self):
        return reverse('platform_admin:market-sector-geo-zone-detail-view', kwargs={'geozone_pk': self.pk})

    def get_list_load_market_sector_geo_zone_details_url(self):
        return reverse('platform_admin:list-load-market-sector-geo-zone-details-view', kwargs={'geozone_pk': self.pk})


    def get_geo_physical_geo_zone_detail_url(self):
        return reverse('platform_admin:geo-physical-geo-zone-detail-view', kwargs={'geozone_pk': self.pk})

    def get_list_load_geo_physical_geo_zone_details_url(self):
        return reverse('platform_admin:list-load-geo-physical-geo-zone-details-view', kwargs={'geozone_pk': self.pk})

    def get_market_sector_geo_political_zone_create_view_url(self):
        return reverse('platform_admin:market-sector-geo-political-zone-create-view', kwargs={'geozone_pk': self.pk})

    def get_historical_geo_political_zone_create_view_url(self):
        return reverse('platform_admin:historical-geo-political-zone-create-view', kwargs={'geozone_pk': self.pk})

    def get_geo_physical_geo_political_zone_create_view_url(self):
        return reverse('platform_admin:geo-physical-geo-political-zone-create-view', kwargs={'geozone_pk': self.pk})


class State(models.Model):
    country = models.ForeignKey(Country, null=True, on_delete=models.SET_NULL, related_name='state_countries')
    geo_political_zone = models.ForeignKey(GeoPoliticalZone, null=True, on_delete=models.SET_NULL, related_name='state_geo_political_zones')
    name = models.CharField(max_length=255)
    managers = models.ManyToManyField("accounts.Profile", blank=True, related_name='state_managers')
    is_deleted = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    objects = models.Manager() 
    my_objects = CountryManager()

    def __str__(self):
        return self.name
        
    class Meta:
        verbose_name_plural = 'States'

    class Meta:
        ordering = ['name',]


    def get_historical_state_location_detail_url(self):
        return reverse('platform_admin:historical-state-location-detail-view', kwargs={'state_location_pk': self.pk})

    def get_list_load_historical_state_location_details_url(self):
        return reverse('platform_admin:list-load-historical-state-location-details-view', kwargs={'state_location_pk': self.pk})


    def get_market_sector_state_location_detail_url(self):
        return reverse('platform_admin:market-sector-state-location-detail-view', kwargs={'state_location_pk': self.pk})

    def get_list_load_market_sector_state_location_details_url(self):
        return reverse('platform_admin:list-load-market-sector-state-location-details-view', kwargs={'state_location_pk': self.pk})


    def get_geo_physical_state_location_detail_url(self):
        return reverse('platform_admin:geo-physical-state-location-detail-view', kwargs={'state_location_pk': self.pk})

    def get_list_load_geo_physical_state_location_details_url(self):
        return reverse('platform_admin:list-load-geo-physical-state-location-details-view', kwargs={'state_location_pk': self.pk})

    def get_market_sector_state_create_view_url(self):
        return reverse('platform_admin:market-sector-state-create-view', kwargs={'state_location_pk': self.pk})

    def get_historical_state_create_view_url(self):
        return reverse('platform_admin:historical-state-create-view', kwargs={'state_location_pk': self.pk})

    def get_geo_physical_state_create_view_url(self):
        return reverse('platform_admin:geo-physical-state-create-view', kwargs={'state_location_pk': self.pk})


# Also the LGAs/Towns
class City(models.Model):
    country = models.ForeignKey(Country, null=True, on_delete=models.SET_NULL, related_name='city_countries')
    geo_political_zone = models.ForeignKey(GeoPoliticalZone, null=True, on_delete=models.SET_NULL, related_name='city_geo_political_zones')
    state = models.ForeignKey(State, null=True, on_delete=models.SET_NULL, related_name='city_states')
    tribe = models.ForeignKey(Tribe, blank=True, null=True, on_delete=models.SET_NULL, related_name='city_tribes')
    name = models.CharField(max_length=255)
    managers = models.ManyToManyField("accounts.Profile", blank=True, related_name='city_managers')
    is_deleted = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    objects = models.Manager() 
    my_objects = CountryManager()

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Cities"
        ordering = ['name',]


    def get_historical_city_location_detail_url(self):
        return reverse('platform_admin:historical-city-location-detail-view', kwargs={'city_location_pk': self.pk})

    def get_list_load_historical_city_location_details_url(self):
        return reverse('platform_admin:list-load-historical-city-location-details-view', kwargs={'city_location_pk': self.pk})


    def get_market_sector_city_location_detail_url(self):
        return reverse('platform_admin:market-sector-city-location-detail-view', kwargs={'city_location_pk': self.pk})

    def get_list_load_market_sector_city_location_details_url(self):
        return reverse('platform_admin:list-load-market-sector-city-location-details-view', kwargs={'city_location_pk': self.pk})


    def get_geo_physical_city_location_detail_url(self):
        return reverse('platform_admin:geo-physical-city-location-detail-view', kwargs={'city_location_pk': self.pk})

    def get_list_load_geo_physical_city_location_details_url(self):
        return reverse('platform_admin:list-load-geo-physical-city-location-details-view', kwargs={'city_location_pk': self.pk})

    def get_market_sector_city_create_view_url(self):
        return reverse('platform_admin:market-sector-city-create-view', kwargs={'city_location_pk': self.pk})

    def get_historical_city_create_view_url(self):
        return reverse('platform_admin:historical-city-create-view', kwargs={'city_location_pk': self.pk})

    def get_geo_physical_city_create_view_url(self):
        return reverse('platform_admin:geo-physical-city-create-view', kwargs={'city_location_pk': self.pk})
    

import re

NODE_TYPE_CHOICES = (
    ('MAJOR_ROAD', 'Major Road (MR)'),
    ('SUB_ROAD', 'Sub Road (SR)'),
    ('STREET', 'Street (STR)'),
    ('CLOSE', 'Close / Crescent (CLS)'),
    ('SUB_CLAN', 'Sub-Clan / Community (SB)'),
    ('COMMUNITY', 'Community / Village (SB)'),
    ('LINK_ROAD', 'Sub / Link Road (SR)'),
    ('META_ROAD', 'Meta Road (MR)'),
    ('BUILDING', 'Building (BLD)'),
    ('BUSINESS', 'Business (BIZ)'),
    ('FACILITY', 'Facility (FAC)'),
    ('LANDMARK', 'Landmark (LMK)'),
    ('OTHER', 'Other Territorial Node (NOD)'),
)

NODE_TYPE_PREFIXES = {
    'MAJOR_ROAD': 'MR',
    'SUB_ROAD': 'SR',
    'STREET': 'STR',
    'CLOSE': 'CLS',
    'SUB_CLAN': 'SB',
    'COMMUNITY': 'SB',
    'LINK_ROAD': 'SR',
    'META_ROAD': 'MR',
    'CLAN': 'CLN',
    'BUILDING': 'BLD',
    'BUSINESS': 'BIZ',
    'FACILITY': 'FAC',
    'LANDMARK': 'LMK',
    'OTHER': 'NOD',
}

ROAD_SURFACE_CHOICES = (
    ('ASPHALT', 'Paved / Asphalt'),
    ('INTERLOCKED', 'Interlocked Paving Stones'),
    ('CONCRETE', 'Rigid Concrete Pavement'),
    ('EARTH_ROAD', 'Unpaved / Earth / Laterite'),
    ('GRAVEL', 'Gravel / Crushed Stone'),
    ('DILAPIDATED', 'Dilapidated / Failed Road'),
    ('OTHER', 'Other Surface'),
)

ROAD_CONDITION_CHOICES = (
    ('EXCELLENT', 'Excellent (Newly Paved / No Potholes)'),
    ('GOOD', 'Good (Minor Wear / Fully Motorrable)'),
    ('FAIR', 'Fair (Moderate Potholes / Motorrable with Caution)'),
    ('POOR', 'Poor (Severe Potholes / Eroded)'),
    ('CRITICAL', 'Critical / Impassable / Flooded'),
)

INFRASTRUCTURE_TYPE_CHOICES = (
    ('DRAINAGE', 'Drainage / Storm Water Channel'),
    ('STREET_LIGHT', 'Street Lighting (Solar / Grid)'),
    ('POWER_TRANSFORMER', 'Power Transformer / Distribution Grid'),
    ('WATER_SUPPLY', 'Public Water Supply / Borehole Tap'),
    ('SECURITY_POST', 'Security Gate / Checkpoint / Barrier'),
    ('WASTE_DISPOSAL', 'Waste Disposal / Dump Point'),
    ('SIDEWALK', 'Sidewalk / Pedestrian Walkway'),
    ('SPEED_BUMP', 'Speed Bumps / Traffic Calming'),
    ('TELECOM_INFRASTRUCTURE', 'Telecom Mast / Fiber Distribution Box'),
    ('BRIDGE_CULVERT', 'Bridge / Culvert / Canal Crossing'),
    ('TRAFFIC_LIGHT', 'Traffic Light / Signal'),
    ('OTHER', 'Other Territorial Infrastructure'),
)

INFRASTRUCTURE_STATUS_CHOICES = (
    ('OPERATIONAL', 'Operational / Good Condition'),
    ('NEEDS_MAINTENANCE', 'Needs Maintenance / Minor Repairs'),
    ('CRITICAL', 'Damaged / Dysfunctional / Flooded'),
    ('UNDER_CONSTRUCTION', 'Under Construction / In Progress'),
    ('ABANDONED', 'Abandoned / Defunct'),
)

SIDE_OF_ROAD_CHOICES = (
    ('BOTH', 'Both Sides of Road'),
    ('LEFT', 'Left Side'),
    ('RIGHT', 'Right Side'),
    ('MEDIAN', 'Median / Center Island'),
    ('INTERSECTION', 'Intersection / Crossing'),
    ('NOT_APPLICABLE', 'Not Applicable'),
)


def generate_territory_code(name):
    """
    Derives standard 3-character uppercase alphanumeric code from a territorial name.
    e.g. 'Rumuigbo' -> 'RUM', 'State Housing Estate' -> 'SHE'
    """
    if not name:
        return "NOD"
    words = [w for w in re.split(r'[^A-Za-z0-9]+', name) if w]
    if len(words) >= 3:
        code = "".join([w[0] for w in words[:3]]).upper()
    elif len(words) == 2:
        code = (words[0][:2] + words[1][0]).upper()
    elif len(words) == 1:
        code = words[0][:3].upper()
    else:
        code = "NOD"
    return code if len(code) == 3 else code.ljust(3, 'X')[:3]


class Clan(models.Model):
    country = models.ForeignKey(Country, null=True, blank=True, on_delete=models.SET_NULL, related_name='clan_countries')
    geo_political_zone = models.ForeignKey(GeoPoliticalZone, null=True, blank=True, on_delete=models.SET_NULL, related_name='clan_geo_political_zones')
    state = models.ForeignKey(State, null=True, blank=True, on_delete=models.SET_NULL, related_name='clan_states')
    city = models.ForeignKey(City, null=True, blank=True, on_delete=models.SET_NULL, related_name='clan_cities')
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=20, blank=True, null=True, help_text="Territory code prefix, e.g. RUM")
    node_id = models.CharField(max_length=150, blank=True, null=True, db_index=True, help_text="Territorial Node ID, e.g. NG/SS/RIV/OBIO-AKPOR/CLN/001")
    managers = models.ManyToManyField("accounts.Profile", blank=True, related_name='clan_managers')
    restricted_users = models.ManyToManyField("accounts.Profile", blank=True, related_name='clan_restricted_users')
    is_deleted = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    objects = models.Manager() 
    my_objects = CountryManager()

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Clans"
        ordering = ['name',]

    @property
    def display_node_id(self):
        if self.node_id:
            return self.node_id
        if self.state or self.city:
            return self.generate_next_node_id()
        prefix = self.code or generate_territory_code(self.name)
        return f"{prefix}-CLN-{self.id:03d}" if self.id else f"{prefix}-CLN-001"

    def generate_next_node_id(self):
        from .territory_codes import build_clan_node_prefix
        state = self.state
        if not state and self.city and self.city.state:
            state = self.city.state
        geo_zone = self.geo_political_zone
        if not geo_zone and state and state.geo_political_zone:
            geo_zone = state.geo_political_zone

        pattern_prefix = build_clan_node_prefix(
            country=self.country,
            geo_zone=geo_zone,
            state=state,
            city=self.city
        )
        existing = Clan.objects.filter(node_id__startswith=pattern_prefix)
        max_seq = 0
        for c in existing:
            if c.node_id:
                m = re.search(rf"{re.escape(pattern_prefix)}(\d+)", c.node_id)
                if m:
                    try:
                        seq_val = int(m.group(1))
                        if seq_val > max_seq:
                            max_seq = seq_val
                    except ValueError:
                        pass
        return f"{pattern_prefix}{max_seq + 1:03d}"

    def save(self, *args, **kwargs):
        if not self.code and self.name:
            self.code = generate_territory_code(self.name)
        if not self.node_id:
            self.node_id = self.generate_next_node_id()
        super().save(*args, **kwargs)

    def get_historical_clan_location_detail_url(self):
        return reverse('platform_admin:historical-clan-location-detail-view', kwargs={'clan_location_pk': self.pk})

    def get_list_load_historical_clan_location_details_url(self):
        return reverse('platform_admin:list-load-historical-clan-location-details-view', kwargs={'clan_location_pk': self.pk})

    def get_market_sector_clan_location_detail_url(self):
        return reverse('platform_admin:market-sector-clan-location-detail-view', kwargs={'clan_location_pk': self.pk})

    def get_list_load_market_sector_clan_location_details_url(self):
        return reverse('platform_admin:list-load-market-sector-clan-location-details-view', kwargs={'clan_location_pk': self.pk})

    def get_geo_physical_clan_location_detail_url(self):
        return reverse('platform_admin:geo-physical-clan-location-detail-view', kwargs={'clan_location_pk': self.pk})

    def get_list_load_geo_physical_clan_location_details_url(self):
        return reverse('platform_admin:list-load-geo-physical-clan-location-details-view', kwargs={'clan_location_pk': self.pk})

    def get_market_sector_clan_create_view_url(self):
        return reverse('platform_admin:market-sector-clan-create-view', kwargs={'clan_location_pk': self.pk})

    def get_historical_clan_create_view_url(self):
        return reverse('platform_admin:historical-clan-create-view', kwargs={'clan_location_pk': self.pk})

    def get_geo_physical_clan_create_view_url(self):
        return reverse('platform_admin:geo-physical-clan-create-view', kwargs={'clan_location_pk': self.pk})
    

class SubClan(models.Model):
    country = models.ForeignKey(Country, null=True, blank=True, on_delete=models.SET_NULL)
    geo_political_zone = models.ForeignKey(GeoPoliticalZone, null=True, blank=True, on_delete=models.SET_NULL)
    state = models.ForeignKey(State, null=True, blank=True, on_delete=models.SET_NULL)
    city = models.ForeignKey(City, null=True, blank=True, on_delete=models.SET_NULL)
    clan = models.ForeignKey(Clan, null=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=255)
    node_type = models.CharField(max_length=50, default='STREET', choices=NODE_TYPE_CHOICES, help_text="Territorial node classification")
    node_id = models.CharField(max_length=150, blank=True, null=True, db_index=True, help_text="Territorial Node ID, e.g. NG/SS/RIV/OBIO-AKPOR/CLN/001/SB/001")
    parent_road = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='connected_streets',
        help_text="Major road, meta road, or link road this street/close connects to"
    )
    road_surface = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        choices=ROAD_SURFACE_CHOICES,
        default='ASPHALT',
        help_text="Surface type of the road (e.g. Asphalt, Interlocked, Earth)"
    )
    road_condition = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        choices=ROAD_CONDITION_CHOICES,
        default='GOOD',
        help_text="Overall condition of the road"
    )
    managers = models.ManyToManyField("accounts.Profile", blank=True, related_name='subclan_managers')
    restricted_users = models.ManyToManyField("accounts.Profile", blank=True, related_name='subclan_restricted_users')
    is_deleted = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    objects = models.Manager() 
    my_objects = CountryManager()

    def __str__(self):
        return f"{self.name} ({self.display_node_id})"
    
    class Meta:
        verbose_name_plural = "Sub-Clans / Territorial Nodes"
        ordering = ['name',]

    @property
    def display_node_id(self):
        if self.node_id:
            return self.node_id
        from .territory_codes import get_node_type_code
        code = get_node_type_code(self.node_type)
        parent = self.parent_road
        if parent:
            parent_nid = parent.node_id or parent.display_node_id
        elif self.clan:
            parent_nid = self.clan.node_id or self.clan.display_node_id
        else:
            parent_nid = "NOD"
        return f"{parent_nid}/{code}/{self.id:03d}" if self.id else f"{parent_nid}/{code}/001"

    @property
    def total_infrastructures(self):
        return self.infrastructures.filter(is_deleted=False).count()

    @property
    def drainages(self):
        return self.infrastructures.filter(infrastructure_type='DRAINAGE', is_deleted=False)

    @property
    def street_lights(self):
        return self.infrastructures.filter(infrastructure_type='STREET_LIGHT', is_deleted=False)

    def generate_next_node_id(self):
        from .territory_codes import build_road_node_prefix
        parent = self.parent_road
        if parent:
            parent_nid = parent.node_id or parent.display_node_id
        elif self.clan:
            parent_nid = self.clan.node_id or self.clan.display_node_id
        else:
            parent_nid = "NG/SS/RIV/OBIO-AKPOR/CLN/001"

        prefix = build_road_node_prefix(parent_nid, self.node_type)

        # Find existing sequence numbers for this prefix
        existing_node_ids = SubClan.objects.filter(
            node_id__startswith=prefix
        ).values_list('node_id', flat=True)

        max_seq = 0
        pattern = re.compile(rf"^{re.escape(prefix)}(\d+)")
        for nid in existing_node_ids:
            if nid:
                m = pattern.match(nid)
                if m:
                    try:
                        seq_val = int(m.group(1))
                        if seq_val > max_seq:
                            max_seq = seq_val
                    except ValueError:
                        pass
        return f"{prefix}{max_seq + 1:03d}"

    def save(self, *args, **kwargs):
        if not self.node_id:
            self.node_id = self.generate_next_node_id()
        super().save(*args, **kwargs)


class TerritorialInfrastructure(models.Model):
    clan = models.ForeignKey(Clan, on_delete=models.CASCADE, related_name='clan_infrastructures')
    subclan = models.ForeignKey(
        SubClan,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='infrastructures',
        help_text="Specific road/street or territorial node where this infrastructure is located"
    )
    name = models.CharField(max_length=255, help_text="e.g. Concrete Covered Drainage - East Side, 50W Solar Streetlights Section A")
    infrastructure_type = models.CharField(max_length=50, choices=INFRASTRUCTURE_TYPE_CHOICES)
    status = models.CharField(max_length=50, default='OPERATIONAL', choices=INFRASTRUCTURE_STATUS_CHOICES)
    side_of_road = models.CharField(max_length=50, default='BOTH', choices=SIDE_OF_ROAD_CHOICES, blank=True, null=True)
    quantity = models.PositiveIntegerField(default=1, help_text="Number of units, e.g. 15 street light poles")
    coverage_length_meters = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Coverage or length in meters (e.g. for drainage, sidewalk)")
    description = models.TextField(blank=True, null=True)
    installed_by = models.CharField(max_length=255, blank=True, null=True, help_text="e.g. State Government, Community Self-Help, Federal Ministry, Private Developer")
    year_installed = models.PositiveIntegerField(blank=True, null=True)
    gps_coordinates = models.CharField(max_length=100, blank=True, null=True, help_text="Latitude, Longitude (e.g. 4.8156, 7.0498)")
    is_deleted = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    my_objects = CountryManager()

    def __str__(self):
        target = self.subclan.name if self.subclan else (self.clan.name if self.clan else 'Unassigned')
        return f"{self.name} ({self.get_infrastructure_type_display()}) - {target}"

    class Meta:
        verbose_name = "Territorial Infrastructure"
        verbose_name_plural = "Territorial Infrastructures"
        ordering = ['-date_created']
