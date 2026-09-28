from django.contrib import admin

# Register your models here.
from .models import (
    Country, State, City, GeoPoliticalZone, Clan, SubClan, Tribe, TerritorialInfrastructure
)


class ModelAdminPreventDelete(admin.ModelAdmin):
    def has_delete_permission(self, request, obj=None):
        return False
    

class TerritorialInfrastructureInline(admin.TabularInline):
    model = TerritorialInfrastructure
    extra = 1
    fields = ('name', 'infrastructure_type', 'status', 'side_of_road', 'quantity', 'coverage_length_meters', 'installed_by')
    show_change_link = True


class SubClanInline(admin.TabularInline):
    model = SubClan
    extra = 1
    fields = ('name', 'node_type', 'node_id', 'parent_road', 'road_surface', 'road_condition')
    show_change_link = True

class ClanInline(admin.TabularInline):
    model = Clan

class CityInline(admin.TabularInline):
    model = City

class StateInline(admin.TabularInline):
    model = State


class CityAdmin(admin.ModelAdmin):
    inlines = [ClanInline]
    list_display = ('name', 'id')
    search_fields = ['name',]

    def has_delete_permission(self, request, obj=None):
        return False


class ClanAdmin(admin.ModelAdmin):
    inlines = [SubClanInline, TerritorialInfrastructureInline]
    list_display = ('name', 'code', 'node_id', 'id')
    search_fields = ['name', 'code', 'node_id']

    def has_delete_permission(self, request, obj=None):
        return False

class StateAdmin(admin.ModelAdmin):
    inlines = [CityInline]
    list_display = ('name', 'id')
    search_fields = ['name',]

    def has_delete_permission(self, request, obj=None):
        return False


class GeoPoliticalZoneAdmin(admin.ModelAdmin):
    inlines = [StateInline]
    list_display = ('name', 'id')
    search_fields = ['name',]

    def has_delete_permission(self, request, obj=None):
        return False


class TribeAdmin(admin.ModelAdmin):
    inlines = [CityInline]
    list_display = ('name', 'id')
    search_fields = ['name',]

    def has_delete_permission(self, request, obj=None):
        return False
    
    
class SubClanAdmin(admin.ModelAdmin):
    inlines = [TerritorialInfrastructureInline]
    list_display = ('name', 'display_node_id', 'node_type', 'clan', 'parent_road', 'road_surface', 'road_condition', 'total_infrastructures')
    list_filter = ('node_type', 'road_surface', 'road_condition')
    search_fields = ['name', 'node_id', 'clan__name']
    raw_id_fields = ('clan', 'parent_road')

    def has_delete_permission(self, request, obj=None):
        return False


class TerritorialInfrastructureAdmin(admin.ModelAdmin):
    list_display = ('name', 'infrastructure_type', 'clan', 'subclan', 'status', 'side_of_road', 'quantity', 'installed_by', 'date_created')
    list_filter = ('infrastructure_type', 'status', 'side_of_road')
    search_fields = ('name', 'clan__name', 'subclan__name', 'description', 'installed_by')
    raw_id_fields = ('clan', 'subclan')


admin.site.register(Country, ModelAdminPreventDelete)
admin.site.register(Tribe, TribeAdmin)
admin.site.register(GeoPoliticalZone, GeoPoliticalZoneAdmin)
admin.site.register(State, StateAdmin)
admin.site.register(City, CityAdmin)
admin.site.register(Clan, ClanAdmin)
admin.site.register(SubClan, SubClanAdmin)
admin.site.register(TerritorialInfrastructure, TerritorialInfrastructureAdmin)