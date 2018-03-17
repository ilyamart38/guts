from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, Http404
from django.views import generic
from .models import MGS, CAMPUS, THREAD
from django.contrib.auth.mixins import LoginRequiredMixin

# Класс заглавного представления приложения
class IndexView(LoginRequiredMixin, generic.ListView):
    template_name = 'network/index.html'
    context_object_name = 'mgs_list'

    def get_queryset(self):
        return MGS.objects.order_by('title')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Количество посещений представления CampusView
        context['num_visits'] = self.request.session.get('num_visits', 0)
        self.request.session['num_visits'] = context['num_visits']+1
        return context

# Клас представления для МГС
class MgsView(LoginRequiredMixin, generic.DetailView):
    model = MGS
    template_name = 'network/mgs.html'

# Клас представления для кампуса
class CampusView(LoginRequiredMixin, generic.DetailView):
    model = CAMPUS
    template_name = 'network/campus.html'
    
class ThreadView(LoginRequiredMixin, generic.DetailView):
    model = THREAD
	
## Клас представления для сервисов IPoE
#class IPoEView(generic.ListView):
#    model = IPOE_SERVICESS

## Клас представления для сервисов L2
#class L2View(generic.ListView):
#    model = IPOE_SERVICESS

def campus_view(request, pk):
    response = "Кампус_id %s."
    return HttpResponse(response % campus_id)
