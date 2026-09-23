from django.contrib import admin
from .models import (MarketSectorBulkData, MarketSector, Historical, 
                    HistoricalCategory, MarketSectorCategory, 
                    GeoPhysicalCategory,
                    GeoPhysicalData, MarketSectorSubCategory
                )


class ModelAdminPreventDelete(admin.ModelAdmin):
    def has_delete_permission(self, request, obj=None):
        return False


class MarketSectorAdmin(admin.ModelAdmin):
    list_display = ('id', 'is_deleted', 'user', 'category', 'state')
    list_editable = ('is_deleted',)

    def has_delete_permission(self, request, obj=None):
        return False


class GeoPhysicalDataAdmin(admin.ModelAdmin):
    list_display = ('id', 'is_deleted', 'user', 'category', 'state')
    list_editable = ('is_deleted',)

    def has_delete_permission(self, request, obj=None):
        return False


class HistoricalAdmin(admin.ModelAdmin):
    list_display = ('id', 'is_deleted', 'user', 'category', 'state')
    list_editable = ('is_deleted',)

    def has_delete_permission(self, request, obj=None):
        return False

admin.site.register(MarketSectorBulkData, ModelAdminPreventDelete)
admin.site.register(MarketSector, MarketSectorAdmin)

admin.site.register(Historical, HistoricalAdmin)
admin.site.register(GeoPhysicalCategory, ModelAdminPreventDelete)
admin.site.register(HistoricalCategory, ModelAdminPreventDelete)

admin.site.register(GeoPhysicalData, GeoPhysicalDataAdmin)
admin.site.register(MarketSectorCategory, ModelAdminPreventDelete)
admin.site.register(MarketSectorSubCategory, ModelAdminPreventDelete)