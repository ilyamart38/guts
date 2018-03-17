from django.shortcuts import render
from django.views import generic
from .models import L2_SERVICES
from django.contrib.auth.mixins import LoginRequiredMixin

# Create your views here.

# Класс заглавного представления приложения
class IndexView(LoginRequiredMixin, generic.ListView):
    template_name = 'l2/index.html'
    context_object_name = 'l2_services_list'

    def get_queryset(self):
        return L2_SERVICES.objects.order_by('client')
