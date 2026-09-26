from django.contrib import admin

from .models import Contact, Profile


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    pass


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    pass
