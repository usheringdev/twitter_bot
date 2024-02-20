from django.contrib import admin

from main.models import APOD


@admin.register(APOD)
class APODAdmin(admin.ModelAdmin):
    pass
