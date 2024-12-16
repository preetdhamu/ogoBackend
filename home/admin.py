from django.contrib import admin

# Register your models here.

from django.contrib import admin
from .models import CustomUser,Video

admin.site.register(CustomUser)
admin.site.register(Video)