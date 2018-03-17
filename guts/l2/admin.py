from django.contrib import admin

# Register your models here.
from .models import L2_SERVICES, SHG

admin.site.register(L2_SERVICES)
admin.site.register(SHG)