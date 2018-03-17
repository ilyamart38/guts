from django.db import models
from clients.models import CLIENTS
from network.models import SAP

# Create your models here.
# (13) Класс услуг L2
class L2_SERVICES(models.Model):
	vpls = models.IntegerField(unique = True)
	client = models.ForeignKey(CLIENTS, on_delete = models.CASCADE)
	sap = models.ManyToManyField(SAP)

# (14) Класс описывающий сплит-горизонты для L2_SERVICES
class SHG(models.Model):
	title = models.CharField(max_length=100)
	vpls = models.ForeignKey(L2_SERVICES, on_delete=models.CASCADE)
	