from django.contrib import admin

from simple_history.admin import SimpleHistoryAdmin
# Импортируем нужные классы для админки
from .models import LAG, SAP, MGS, MS, CAMPUS, THREAD, SUBNET, SW_MODEL, ACCESS_NODE, ACCESS_SWITCH, VENDORS, GUTS_NETWORK, PORT_TYPE, PORT_OF_ACCESS_SWITCH


admin.site.register(GUTS_NETWORK)
admin.site.register(VENDORS)
admin.site.register(LAG)
admin.site.register(SAP)
admin.site.register(MGS)
admin.site.register(MS)
admin.site.register(CAMPUS)
admin.site.register(THREAD)
admin.site.register(SUBNET)
admin.site.register(SW_MODEL, SimpleHistoryAdmin)
admin.site.register(ACCESS_NODE)
admin.site.register(ACCESS_SWITCH, SimpleHistoryAdmin)
admin.site.register(PORT_TYPE)
admin.site.register(PORT_OF_ACCESS_SWITCH, SimpleHistoryAdmin)
