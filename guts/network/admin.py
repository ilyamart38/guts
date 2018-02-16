from django.contrib import admin

# Импортируем нужные классы для админки
from .models import MGS, CAMPUS, THREAD, SUBNET

admin.site.register(MGS)
admin.site.register(CAMPUS)
admin.site.register(THREAD)
admin.site.register(SUBNET)
