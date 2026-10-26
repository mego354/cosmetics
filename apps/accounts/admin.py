from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, CustomerProfile, Address


class CustomerProfileInline(admin.StackedInline):
    model = CustomerProfile
    can_delete = False


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = [CustomerProfileInline]
    list_display = ('username', 'email', 'first_name', 'last_name', 'phone_number', 'is_staff')
    search_fields = ('username', 'email', 'phone_number')


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'user', 'governorate', 'city', 'phone_number', 'is_default')
    list_filter = ('governorate', 'is_default')
    search_fields = ('full_name', 'phone_number', 'city', 'street_address')
