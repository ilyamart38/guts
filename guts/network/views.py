from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.urls import reverse
from django.views import generic
from .models import MGS, MS, CAMPUS, THREAD
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .forms import Campus_Form, Thread_Form
from . import net_lib

# Класс заглавного представления приложения
class IndexView(LoginRequiredMixin, generic.ListView):
    template_name = 'network/index.html'
    context_object_name = 'mgs_list'

    def get_queryset(self):
        return MGS.objects.order_by('mgs_num')
    
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
   
    # Для корректного отображения списка МГС влевой части добавляем контекст mgs_list в представление
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mgs_list'] = MGS.objects.all()
        return context


# Клас представления для кампуса
class CampusView(LoginRequiredMixin, generic.DetailView):
    model = CAMPUS
    # Для корректного отображения списка МГС влевой части добавляем контекст mgs_list в представление
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mgs_list'] = MGS.objects.all()
        return context
    
class ThreadView(LoginRequiredMixin, generic.DetailView):
    model = THREAD

def NewCampusInMs(request, mgs_id, ms_id):
    mgs = MGS.objects.get(id=mgs_id)
    ms = MS.objects.get(id=ms_id)
    if request.method == 'POST':
        form = Campus_Form(request.POST)
        if form.is_valid():
            campus = form.save(commit=False)
            campus.save()
            return redirect('mgs', pk=mgs.id)
    else:
        num_in_ms=1
        while CAMPUS.objects.filter(num_in_ms=num_in_ms, ms = ms):
            num_in_ms += 1
        form = Campus_Form(initial = {'ms': ms_id, 'num_in_ms': num_in_ms})
        form.mgs = mgs_id
    return render(request, 'network/campus_form.html', {'form': form})

class CampusUpdate(UpdateView):
    model = CAMPUS
    fields = ('prefix', 'ms', 'num_in_ms')

class CampusCreate(CreateView):
    model = CAMPUS
    fields = ('ms', 'num_in_ms')

class CampusDelete(DeleteView):
    model=CAMPUS
    #success_url = reverse_lazy('mgs')
    
    def delete(self, request, *args, **kwargs):
        campus_id = self.kwargs['pk']

        campus = CAMPUS.objects.get(id=campus_id)
        mgs_id = campus.ms.mgs.id
        campus.delete()

        return HttpResponseRedirect(reverse('mgs', kwargs={'pk': mgs_id}))

def NewMsInMgs(request, mgs_id):
    mgs = MGS.objects.get(id=mgs_id)
    if request.method == 'POST':
        form = Ms_Form(request.POST)
        if form.is_valid():
            campus = form.save(commit=False)
            campus.save()
            return redirect('mgs', pk=mgs.id)
    else:
        num_in_mgs=1
        while MS.objects.filter(num_in_mgs=num_in_mgs):
            num_in_mgs += 1
        form = Ms_Form(initial = {'mgs': mgs_id, 'num_in_mgs': num_in_mgs})
    return render(request, 'network/campus_form.html', {'form': form})

class MsDelete(DeleteView):
    model=MS
    #success_url = reverse_lazy('mgs')
    
    def delete(self, request, *args, **kwargs):
        ms_id = self.kwargs['pk']

        ms = MS.objects.get(id=ms_id)
        mgs_id = ms.mgs.id
        ms.delete()

        return HttpResponseRedirect(reverse('mgs', kwargs={'pk': mgs_id}))

def NewThreadInCampus(request, campus_id):
    campus = CAMPUS.objects.get(id=campus_id)
    if request.method == 'POST':
        form = Thread_Form(request.POST)
        if form.is_valid():
            campus = form.save(commit=False)
            campus.save()
            return redirect('campus', pk=campus_id)
    else:
        num_in_campus=1
        while THREAD.objects.filter(campus=campus, num_in_campus=num_in_campus):
            num_in_campus += 1
        outvlan = net_lib.calculation_outvlan(campus.ms.mgs.mgs_num, campus.ms.num_in_mgs, campus.num_in_ms, num_in_campus)
        mapvlan = net_lib.calculation_mapvlan(campus.ms.num_in_mgs, campus.num_in_ms, num_in_campus)
        # Если номер кампуса не концептуален, ищем свободную нитку за пределами концепции (х.7.7 - х.8.8)
        for calc_ms in (7,8):
            for calc_campus in range(1,9):
                # исключаем x.7.1-x.7.6
                if not(calc_ms == 7 and calc_campus in range(1,7)):
                    for calc_thread in range(1,5):
                        calc_outvlan = net_lib.calculation_outvlan(campus.ms.mgs.mgs_num, calc_ms, calc_campus, calc_thread)
                        # проверяем свободна ли нитка
                        if not THREAD.objects.filter(outvlan=calc_outvlan):
                            outvlan = calc_outvlan
                            mapvlan = net_lib.calculation_mapvlan(calc_ms, calc_campus, calc_thread)
                        # Если outvlan и mapvlan не пустые то выходим из цыкла
                        if outvlan and mapvlan:
                            break
                if outvlan and mapvlan:
                    break
            if outvlan and mapvlan:
                break
        form = Thread_Form(initial = 
            {
            'campus': campus_id, 
            'num_in_campus': num_in_campus,
            'mapvlan': mapvlan,
            'outvlan': outvlan,
            })
    return render(request, 'network/thread_form.html', {'form': form})

class ThreadUpdate(UpdateView):
    model = THREAD
    fields = ('campus', 'num_in_campus', 'outvlan', 'mapvlan')

class ThreadDelete(DeleteView):
    model=THREAD
    #success_url = reverse_lazy('mgs')
    
    def delete(self, request, *args, **kwargs):
        tread_id = self.kwargs['pk']

        thread = THREAD.objects.get(id=tread_id)
        campus_id = thread.campus.id
        thread.delete()

        return HttpResponseRedirect(reverse('campus', kwargs={'pk': campus_id}))
