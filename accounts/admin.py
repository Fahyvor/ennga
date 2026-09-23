from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from accounts.models import Account, Profile

class ModelAdminPreventDelete(admin.ModelAdmin):
    def has_delete_permission(self, request, obj=None):
        return False

class AccountAdmin(UserAdmin):
    list_display = ('username', 'is_active', 'email', 'first_name', 'last_name', 'is_staff')
    list_editable = ('email',)
    search_fields = ('email', 'username')
    readonly_fields = ("id", "date_joined", "last_login")

    filter_horizontal = ()
    fieldsets = ()
    ordering = ('-date_joined',)

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(Account, AccountAdmin)
admin.site.register(Profile, ModelAdminPreventDelete)