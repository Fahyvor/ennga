from django.db import models
from accounts.models import Profile
from utility.models import Country, State, City, GeoPoliticalZone
from ckeditor_uploader.fields import RichTextUploadingField
from django.urls import reverse


class MarketSectorCategoryManager(models.Manager):
    def get_queryset(self):
        return super(MarketSectorCategoryManager, self).get_queryset().filter(is_deleted=False)

class MarketSectorCategory(models.Model):
    name = models.CharField(max_length=255)
    is_deleted = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    objects = models.Manager() 
    my_objects = MarketSectorCategoryManager()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Market Sector Categories'

    def get_market_sector_category_detail_url(self):
        return reverse('platform_admin:market-sector-category-detail-view', kwargs={'category_pk': self.pk})

    def get_list_load_market_sector_category_details_url(self):
        return reverse('platform_admin:list-load-market-sector-category-details-view', kwargs={'category_pk': self.pk})


class MarketSectorSubCategoryManager(models.Manager):
    def get_queryset(self):
        return super(MarketSectorSubCategoryManager, self).get_queryset().filter(is_deleted=False)

class MarketSectorSubCategory(models.Model):
    category = models.ForeignKey(MarketSectorCategory, blank=True, null=True, on_delete=models.SET_NULL, related_name='subcategories')
    name = models.CharField(max_length=255)
    is_deleted = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    objects = models.Manager() 
    my_objects = MarketSectorSubCategoryManager()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Market Sector Sub Categories'

    def get_market_sector_subcategory_detail_url(self):
        return reverse('platform_admin:market-sector-subcategory-detail-view', kwargs={'subcategory_pk': self.pk})

    def get_list_load_market_sector_subcategory_details_url(self):
        return reverse('platform_admin:list-load-market-sector-subcategory-details-view', kwargs={'subcategory_pk': self.pk})


class MarketSectorBulkDataManager(models.Manager):
    def get_queryset(self):
        return super(MarketSectorBulkDataManager, self).get_queryset().filter(is_deleted=False)

class MarketSectorBulkData(models.Model):
    user = models.ForeignKey("accounts.Profile", blank=True, null=True, on_delete=models.SET_NULL)
    country = models.ForeignKey("utility.Country", blank=True, null=True, on_delete=models.SET_NULL)
    state = models.ForeignKey("utility.State", blank=True, null=True, on_delete=models.SET_NULL)
    city = models.ForeignKey("utility.City", blank=True, null=True, on_delete=models.SET_NULL)
    category = models.ForeignKey(MarketSectorCategory, null=True, on_delete=models.SET_NULL)
    sub_category = models.ForeignKey(MarketSectorSubCategory, null=True, on_delete=models.SET_NULL)
    filez = models.FileField(upload_to='customers/csv')
    activated = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    objects = models.Manager() 
    my_objects = MarketSectorBulkDataManager()

    def __str__(self):
        return f"File id: {self.id}"
    


class MarketSectorManager(models.Manager):
    def get_queryset(self):
        return super(MarketSectorManager, self).get_queryset().filter(is_deleted=False)

class MarketSector(models.Model):
    user = models.ForeignKey("accounts.Profile", blank=True, null=True, on_delete=models.SET_NULL)
    bulk_data = models.ForeignKey('MarketSectorBulkData', blank=True, null=True, on_delete=models.SET_NULL)
    category = models.ForeignKey(MarketSectorCategory, null=True, on_delete=models.SET_NULL)
    sub_category = models.ForeignKey(MarketSectorSubCategory, null=True, on_delete=models.SET_NULL)
    country = models.ForeignKey("utility.Country", blank=True, null=True, on_delete=models.SET_NULL)
    geo_political_zone = models.ForeignKey(GeoPoliticalZone, null=True, on_delete=models.SET_NULL)
    state = models.ForeignKey("utility.State", blank=True, null=True, on_delete=models.SET_NULL)
    city = models.ForeignKey("utility.City", blank=True, null=True, on_delete=models.SET_NULL)
    clan = models.ForeignKey("utility.Clan", blank=True, null=True, on_delete=models.SET_NULL)
    subclan = models.ForeignKey("utility.SubClan", blank=True, null=True, on_delete=models.SET_NULL)
    description = RichTextUploadingField(blank=True, null=True,)
    is_deleted = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    objects = models.Manager() 
    my_objects = MarketSectorManager()

    def __str__(self):
        return str(self.id)
    
    def get_absolute_url(self):
        return reverse('platform_admin:market-sector-detail-view', kwargs={'pk': self.pk})
    
    def get_delete_data_url(self):
        return reverse('platform_admin:market-sector-delete-data-view', kwargs={'pk': self.pk})



class HistoricalCategoryManager(models.Manager):
    def get_queryset(self):
        return super(HistoricalCategoryManager, self).get_queryset().filter(is_deleted=False)

class HistoricalCategory(models.Model):
    name = models.CharField(max_length=255)
    is_deleted = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    objects = models.Manager() 
    my_objects = HistoricalCategoryManager()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Historical Categories'

    def get_historical_category_detail_url(self):
        return reverse('platform_admin:historical-category-detail-view', kwargs={'category_pk': self.pk})

    def get_list_load_historical_category_details_url(self):
        return reverse('platform_admin:list-load-historical-category-details-view', kwargs={'category_pk': self.pk})



class HistoricalManager(models.Manager):
    def get_queryset(self):
        return super(HistoricalManager, self).get_queryset().filter(is_deleted=False)

class Historical(models.Model):
    user = models.ForeignKey("accounts.Profile", blank=True, null=True, on_delete=models.SET_NULL)
    country = models.ForeignKey("utility.Country", blank=True, null=True, on_delete=models.SET_NULL)
    geo_political_zone = models.ForeignKey(GeoPoliticalZone, null=True, on_delete=models.SET_NULL)
    state = models.ForeignKey("utility.State", blank=True, null=True, on_delete=models.SET_NULL)
    city = models.ForeignKey("utility.City", blank=True, null=True, on_delete=models.SET_NULL)
    clan = models.ForeignKey("utility.Clan", blank=True, null=True, on_delete=models.SET_NULL)
    subclan = models.ForeignKey("utility.SubClan", blank=True, null=True, on_delete=models.SET_NULL)
    category = models.ForeignKey(HistoricalCategory, null=True, on_delete=models.SET_NULL)
    description = RichTextUploadingField(blank=True, null=True,)
    is_deleted = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    objects = models.Manager() 
    my_objects = HistoricalManager()

    def __str__(self):
        return str(self.id)
    
    def get_absolute_url(self):
        return reverse('platform_admin:historical-detail-view', kwargs={'pk': self.pk})
    
    def get_delete_data_url(self):
        return reverse('platform_admin:historical-delete-data-view', kwargs={'pk': self.pk})



class GeoPhysicalCategoryManager(models.Manager):
    def get_queryset(self):
        return super(GeoPhysicalCategoryManager, self).get_queryset().filter(is_deleted=False)

class GeoPhysicalCategory(models.Model):
    name = models.CharField(max_length=255)
    is_deleted = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    objects = models.Manager() 
    my_objects = GeoPhysicalCategoryManager()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Geo Physical Categories'
    
    def get_geo_physical_category_detail_url(self):
        return reverse('platform_admin:geo-physical-category-detail-view', kwargs={'category_pk': self.pk})

    def get_list_load_geo_physical_category_details_url(self):
        return reverse('platform_admin:list-load-geo-physical-category-details-view', kwargs={'category_pk': self.pk})



class GeoPhysicalDataManager(models.Manager):
    def get_queryset(self):
        return super(GeoPhysicalDataManager, self).get_queryset().filter(is_deleted=False)

class GeoPhysicalData(models.Model):
    user = models.ForeignKey("accounts.Profile", blank=True, null=True, on_delete=models.SET_NULL)
    country = models.ForeignKey("utility.Country", blank=True, null=True, on_delete=models.SET_NULL)
    geo_political_zone = models.ForeignKey(GeoPoliticalZone, null=True, on_delete=models.SET_NULL)
    state = models.ForeignKey("utility.State", blank=True, null=True, on_delete=models.SET_NULL)
    city = models.ForeignKey("utility.City", blank=True, null=True, on_delete=models.SET_NULL)
    clan = models.ForeignKey("utility.Clan", blank=True, null=True, on_delete=models.SET_NULL)
    subclan = models.ForeignKey("utility.SubClan", blank=True, null=True, on_delete=models.SET_NULL)
    category = models.ForeignKey(GeoPhysicalCategory, null=True, on_delete=models.SET_NULL)
    description = RichTextUploadingField(blank=True, null=True,)
    is_deleted = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    objects = models.Manager() 
    my_objects = GeoPhysicalDataManager()

    def __str__(self):
        return str(self.id)
    
    def get_absolute_url(self):
        return reverse('platform_admin:geo-physical-detail-view', kwargs={'pk': self.pk})
    
    def get_delete_data_url(self):
        return reverse('platform_admin:geo-physical-delete-data-view', kwargs={'pk': self.pk})