from django.db import models
from network.models import SAP
from clients.models import CLIENTS

# Create your models here.
class IPOE_SERVICESS(models.Model):
	client = models.ForeignKey(CLIENTS, on_delete = models.CASCADE)
	sap = models.ForeignKey(SAP, on_delete = models.SET_NULL, blank=True, null=True)
