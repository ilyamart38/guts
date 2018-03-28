from django.contrib import admin

# Импортируем нужные классы для админки
from .models import LAG, SAP, MGS, MS, CAMPUS, THREAD, SUBNET, SW_MODEL, ACCESS_NODE, ACCESS_SWITCH, VENDORS

admin.site.register(VENDORS)
admin.site.register(LAG)
admin.site.register(SAP)
admin.site.register(MGS)
admin.site.register(MS)
admin.site.register(CAMPUS)
admin.site.register(THREAD)
admin.site.register(SUBNET)
admin.site.register(SW_MODEL)
admin.site.register(ACCESS_NODE)
admin.site.register(ACCESS_SWITCH)

