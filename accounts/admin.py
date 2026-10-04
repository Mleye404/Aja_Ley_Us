from django.contrib import admin
from .models import Profile, Address


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone")


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "city", "country", "user")
    list_filter = ("country", "city")
