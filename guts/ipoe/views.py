from django.shortcuts import render
from django.views import generic
from .models import IPOE_SERVICESS
from django.contrib.auth.mixins import LoginRequiredMixin

# Create your views here.

# Класс заглавного представления приложения
class IndexView(LoginRequiredMixin,  generic.ListView):
    template_name = 'ipoe/index.html'
    context_object_name = 'ipoe_services_list'

    def get_queryset(self):
        return IPOE_SERVICESS.objects.order_by('client')
