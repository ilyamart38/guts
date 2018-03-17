from django.shortcuts import render
from django.views import generic
from .models import CLIENTS
from django.contrib.auth.mixins import LoginRequiredMixin

# Create your views here.

# Класс заглавного представления приложения
class IndexView(LoginRequiredMixin, generic.ListView):
    template_name = 'clients/index.html'
    context_object_name = 'clients_list'

    def get_queryset(self):
        return CLIENTS.objects.order_by('name')
