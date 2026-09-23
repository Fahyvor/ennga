from django.contrib import admin

# Register your models here.
from .models import Country, State, City, GeoPoliticalZone, Clan, SubClan, Tribe


class ModelAdminPreventDelete(admin.ModelAdmin):
    def has_delete_permission(self, request, obj=None):
        return False
    

class SubClanInline(admin.TabularInline):
    model = SubClan

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
    # list_editable = ('quiz',)

    def has_delete_permission(self, request, obj=None):
        return False


class ClanAdmin(admin.ModelAdmin):
    inlines = [SubClanInline]
    list_display = ('name', 'id')
    search_fields = ['name',]
    # list_editable = ('quiz',)

    def has_delete_permission(self, request, obj=None):
        return False

class StateAdmin(admin.ModelAdmin):
    inlines = [CityInline]
    list_display = ('name', 'id')
    search_fields = ['name',]
    # list_editable = ('quiz',)

    def has_delete_permission(self, request, obj=None):
        return False


class GeoPoliticalZoneAdmin(admin.ModelAdmin):
    inlines = [StateInline]
    list_display = ('name', 'id')
    search_fields = ['name',]
    # list_editable = ('quiz',)

    def has_delete_permission(self, request, obj=None):
        return False


class TribeAdmin(admin.ModelAdmin):
    inlines = [CityInline]
    list_display = ('name', 'id')
    search_fields = ['name',]
    # list_editable = ('quiz',)

    def has_delete_permission(self, request, obj=None):
        return False
    
    
class SubClanAdmin(admin.ModelAdmin):
    search_fields = ['name',]

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(Country, ModelAdminPreventDelete)
admin.site.register(Tribe, TribeAdmin)
admin.site.register(GeoPoliticalZone, GeoPoliticalZoneAdmin)
admin.site.register(State, StateAdmin)
admin.site.register(City, CityAdmin)
admin.site.register(Clan, ClanAdmin)
admin.site.register(SubClan, SubClanAdmin)