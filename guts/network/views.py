from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.urls import reverse
from django.views import generic
from .models import MGS, MS, CAMPUS, THREAD, SUBNET, ACCESS_NODE, ACCESS_SWITCH, PORT_TYPE, PORT_OF_ACCESS_SWITCH
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.forms import widgets, modelformset_factory

from .forms import Ms_Form, Campus_Form, Thread_Form, SubnetInThread_Form, Node_Form, New_Access_Switch_Form, Ports_Of_Acess_Switch_Formset
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
    #template_name = 'network/mgs.html'
   
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

# Клас представления для нитки    
class ThreadView(LoginRequiredMixin, generic.DetailView):
    model = THREAD

@login_required
def NewCampusInMs(request, mgs_id, ms_id):
    mgs = MGS.objects.get(id=mgs_id)
    ms = MS.objects.get(id=ms_id)
    if request.method == 'POST':
        form = Campus_Form(request.POST)
        if form.is_valid():
            campus = form.save(commit=False)
            campus.save()
            # если создается новый кампус и это ППК, то сразу в ППК создаем четыре нитки
            # если создается МКУ, то добавляем только одну нитку
            if campus.prefix == 'ppk':
                threads_count = 4
            elif campus.prefix == 'mku':
                threads_count = 1
            for num_in_campus in range(1,threads_count+1):
                thread = THREAD(campus=campus, num_in_campus=num_in_campus)
                outvlan = net_lib.calculation_outvlan(campus.ms.mgs.mgs_num, campus.ms.num_in_mgs, campus.num_in_ms, num_in_campus)
                if outvlan:
                    thread.outvlan = outvlan
                mapvlan = net_lib.calculation_mapvlan(campus.ms.num_in_mgs, campus.num_in_ms, num_in_campus)
                if mapvlan:
                    thread.mapvlan = mapvlan
                thread.save()
                # для каждой нитки сразу расчитываем концептуальную подсеть 
                thread_num = thread.num_in_campus
                campus_num = campus.num_in_ms
                ms_num = ms.num_in_mgs
                mgs_num = mgs.mgs_num
                network = net_lib.calculation_subnet(mgs_num, ms_num, campus_num, thread_num)
                if network:
                    subnet = SUBNET(network=network, thread=thread)
                    subnet.save()
                
            return redirect('mgs', pk=mgs.id)
    else:
        num_in_ms=1
        while CAMPUS.objects.filter(num_in_ms=num_in_ms, ms = ms):
            num_in_ms += 1
        form = Campus_Form(initial = {'ms': ms_id, 'num_in_ms': num_in_ms})
        form.mgs = mgs_id
    return render(request, 'network/campus_form.html', {'form': form})

# Клас представления для изменения настроек кампуса
class CampusUpdate(LoginRequiredMixin, UpdateView):
    model = CAMPUS
    fields = ('prefix', 'ms', 'num_in_ms')

# Клас представления для создания кампуса
class CampusCreate(LoginRequiredMixin, CreateView):
    model = CAMPUS
    fields = ('ms', 'num_in_ms')

# Клас представления для удаления кампуса
class CampusDelete(LoginRequiredMixin, DeleteView):
    model=CAMPUS
    #success_url = reverse_lazy('mgs')
    
    def delete(self, request, *args, **kwargs):
        campus_id = self.kwargs['pk']

        campus = CAMPUS.objects.get(id=campus_id)
        mgs_id = campus.ms.mgs.id
        campus.delete()

        return HttpResponseRedirect(reverse('mgs', kwargs={'pk': mgs_id}))

# процедура создания новой МС в текущей МГС
@login_required
def NewMsInMgs(request, mgs_id):
    mgs = MGS.objects.get(id=mgs_id)
    if request.method == 'POST':
        form = Ms_Form(request.POST)
        if form.is_valid():
            ms = form.save(commit=False)
            ms.save()
            return redirect('mgs', pk=mgs.id)
    else:
        num_in_mgs=1
        while MS.objects.filter(mgs=mgs, num_in_mgs=num_in_mgs):
            num_in_mgs += 1
        form = Ms_Form(initial = {'mgs': mgs_id, 'num_in_mgs': num_in_mgs})
    return render(request, 'network/ms_form.html', {'form': form, 'mgs_list':MGS.objects.all()})

# Клас представления для удаления МС
class MsDelete(LoginRequiredMixin, DeleteView):
    model=MS
    
    def delete(self, request, *args, **kwargs):
        ms_id = self.kwargs['pk']

        ms = MS.objects.get(id=ms_id)
        mgs_id = ms.mgs.id
        ms.delete()

        return HttpResponseRedirect(reverse('mgs', kwargs={'pk': mgs_id}))

    def get_context_data(self, **kwargs):
        
        context = super().get_context_data(**kwargs)
        context['mgs_list'] = MGS.objects.all()
        return context

# процедура создания новой нитки в текущем кампусе
@login_required
def NewThreadInCampus(request, campus_id):
    campus = CAMPUS.objects.get(id=campus_id)
    if request.method == 'POST':
        form = Thread_Form(request.POST)
        if form.is_valid():
            thread = form.save(commit=False)
            thread.save()
            # для нитки сразу расчитываем концептуальную подсеть 
            thread_num = thread.num_in_campus
            campus_num = campus.num_in_ms
            ms_num = thread.campus.ms.num_in_mgs
            mgs_num = thread.campus.ms.mgs.mgs_num
            network = net_lib.calculation_subnet(mgs_num, ms_num, campus_num, thread_num)
            if network:
                subnet = SUBNET(network=network, thread=thread)
                subnet.save()
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

# Клас представления для изменения настроек нитки
class ThreadUpdate(LoginRequiredMixin, UpdateView):
    model = THREAD
    fields = ('campus', 'num_in_campus', 'outvlan', 'mapvlan')
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mgs_list'] = MGS.objects.all()
        return context

class ThreadDelete(LoginRequiredMixin, DeleteView):
    model=THREAD
    #success_url = reverse_lazy('mgs')
    
    def delete(self, request, *args, **kwargs):
        tread_id = self.kwargs['pk']

        thread = THREAD.objects.get(id=tread_id)
        campus_id = thread.campus.id
        thread.delete()

        return HttpResponseRedirect(reverse('campus', kwargs={'pk': campus_id}))

# Клас представления для подсети
class SubnetView(LoginRequiredMixin, generic.DetailView):
    model = SUBNET
   
    # Для корректного отображения списка МГС влевой части добавляем контекст mgs_list в представление
    def get_context_data(self, **kwargs):
        
        context = super().get_context_data(**kwargs)
        context['mgs_list'] = MGS.objects.all()
        # получим список всех коммутаторов у которых ip принадлежит нашей подсети
        # сначала получаем список ip-адресов разрешенных в нашей 
        subnet_id = self.kwargs['pk']
        subnet = SUBNET.objects.get(id=subnet_id)
        ip_list = subnet.ip_address()
        context['ip_list'] = ip_list
        context['sw_list'] = ACCESS_SWITCH.objects.filter(ip__in=ip_list)
        return context

@login_required
def SubnetInThread(request, thread_id):
    thread = THREAD.objects.get(id=thread_id)
    if request.method == 'POST':
        form = SubnetInThread_Form(request.POST)
        if form.is_valid():
            campus = form.save(commit=False)
            campus.save()
            return redirect('campus', pk=thread.campus.id)
    else:
        thread_num = thread.num_in_campus
        campus_num = thread.campus.num_in_ms
        ms_num = thread.campus.ms.num_in_mgs
        mgs_num = thread.campus.ms.mgs.mgs_num
        network = net_lib.calculation_subnet(mgs_num, ms_num, campus_num, thread_num)
        if SUBNET.objects.filter(network=network).count() > 0:
            network = None
        form = SubnetInThread_Form(initial = 
            {
            'thread': thread_id,
            'network': network,
            })
    return render(request, 'network/net_in_thread_form.html', {'form': form})

class SubnetDelete(DeleteView):
    model=SUBNET
    
    def delete(self, request, *args, **kwargs):
        subnet_id = self.kwargs['pk']

        subnet = SUBNET.objects.get(id=subnet_id)
        campus_id = subnet.thread.campus.id
        subnet.delete()

        return HttpResponseRedirect(reverse('campus', kwargs={'pk': campus_id}))

# процедура создания нового узла в текущей нитке
@login_required
def NewAccessNodeInThread(request, thread_id):
    thread = THREAD.objects.get(id=thread_id)
    mgs_list = MGS.objects.all()
    if request.method == 'POST':
        form = Node_Form(request.POST)
        if form.is_valid():
            node = form.save(commit=False)
            node.save()
            return redirect('campus', pk=thread.campus.id)
    else:
        form = Node_Form( initial =
            {
            'thread':thread_id
            })
    return render(request, 'network/access_node_form.html', {'form': form, 'mgs_list': mgs_list, 'thread':thread})

# Клас представления для изменения узла доступа
class AccessNodeUpdate(LoginRequiredMixin, UpdateView):
    model = ACCESS_NODE
    fields = ('address', 'thread')
    # Для корректного отображения списка МГС влевой части добавляем контекст mgs_list в представление
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mgs_list'] = MGS.objects.all()
        # так же понадобится информация о нитке в которой расположена нода
        node_id = self.kwargs['pk']
        access_node = ACCESS_NODE.objects.get(id=node_id)
        thread = access_node.thread
        context['thread'] = thread
        return context

class AccessNodeDelete(DeleteView):
    model=ACCESS_NODE
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mgs_list'] = MGS.objects.all()
        return context

    def delete(self, request, *args, **kwargs):
        access_node_id = self.kwargs['pk']

        access_node = ACCESS_NODE.objects.get(id=access_node_id)
        campus_id = access_node.thread.campus.id
        access_node.delete()

        return HttpResponseRedirect(reverse('campus', kwargs={'pk': campus_id}))

# процедура создания нового узла в текущей нитке
@login_required
def NewAccessSwitchInNode(request, access_node_id):
    access_node = ACCESS_NODE.objects.get(id=access_node_id)
    mgs_list = MGS.objects.all()
    # Необходимо сформировать список ip-адресов из незанятых в данной нитке
    ip_list=[]
    for subnet in SUBNET.objects.filter(thread=access_node.thread):
        for ip in subnet.ip_address():
            if not ACCESS_SWITCH.objects.filter(ip=ip):
                choice = (str(ip), str(ip))
                ip_list.append(choice)
    if request.method == 'POST':
        form = New_Access_Switch_Form(request.POST)
        if form.is_valid():
            node = form.save(commit=False)
            node.save()
            return redirect('campus', pk=access_node.thread.campus.id)
    else:
        form = New_Access_Switch_Form( initial =
            {
            'access_node':access_node_id,
            })
        form.fields['ip'].widget = widgets.Select(choices=ip_list)

    return render(request, 'network/new_access_switch_in_node.html', {'form': form, 'mgs_list': mgs_list, 'access_node':access_node})

# Клас представления для коммутатора доступа    
class AccessSwitchView(LoginRequiredMixin, generic.DetailView):
    model = ACCESS_SWITCH
   
    # Для корректного отображения списка МГС влевой части добавляем контекст mgs_list в представление
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mgs_list'] = MGS.objects.all()
        context['port_types'] = PORT_TYPE.objects.all()
        access_switch_id = self.kwargs['pk']
        access_switch = ACCESS_SWITCH.objects.get(id=access_switch_id)
        context['access_switch'] = access_switch
        form_set = Ports_Of_Acess_Switch_Formset(queryset=PORT_OF_ACCESS_SWITCH.objects.filter(access_switch=access_switch))
        for form in form_set:
            # если порт pppoe, сигнализатор, магистральный, распределительный или неисправный, то блокируем поле t_vlans
            if form['port_type'].value() in (0, 1, 3, 5, 99):
                form.fields['t_vlans'].widget.attrs['readonly'] = True
            if form['port_type'].value() in (5, 99,0, 1):
                form.fields['u_vlan'].widget.attrs['readonly'] = True
        context['form_set'] = form_set
        
        return context
    def post(self, request, *args, **kwargs):
        access_switch_id = self.kwargs['pk']
        
        form_set = Ports_Of_Acess_Switch_Formset(request.POST)
        if form_set.is_valid():
            #print('OK')
            for form in form_set:
                form.save()
            # после сохранения всех настроек на портах, необходимо обновить настройки всех магистральных портов в нитке
            uplink_ports_in_thread = PORT_OF_ACCESS_SWITCH.objects.filter(
                port_type__in = PORT_TYPE.objects.filter(id__in = (0,1)),
                access_switch__in = ACCESS_SWITCH.objects.filter(
                    access_node__in = ACCESS_NODE.objects.filter(thread = ACCESS_SWITCH.objects.get(id = access_switch_id).access_node.thread)
                )
            )
            print(uplink_ports_in_thread)
            for port in uplink_ports_in_thread:
                port.save_uplink()
            return redirect('access_switch', pk=access_switch_id)
        else:
            #print('NE OK!!!')
            #print('REQUEST', request.POST)
            #for form in form_set:
            #    print('FORM', form)
            #    print('IS_VALID', form.is_valid())
            #    print('FORM_ERRORS', form.errors)
                
            self.object = self.get_object()
            context = super().get_context_data(**kwargs)
            context['form_set'] = form_set
            print('FORM_SET_ERROR_COUNT', form_set.total_error_count())
            return self.render_to_response(context=context)

class AccessSwitchDelete(DeleteView):
    model=ACCESS_SWITCH
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mgs_list'] = MGS.objects.all()
        return context

    def delete(self, request, *args, **kwargs):
        access_switch_id = self.kwargs['pk']

        access_switch = ACCESS_SWITCH.objects.get(id=access_switch_id)
        campus_id = access_switch.access_node.thread.campus.id
        access_switch.delete()

        return HttpResponseRedirect(reverse('campus', kwargs={'pk': campus_id}))

# Клас представления для изменения коммутатора доступа
class AccessSwitchModel(LoginRequiredMixin, UpdateView):
    model = ACCESS_SWITCH
    fields = ('sw_model',)
    # Для корректного отображения списка МГС влевой части добавляем контекст mgs_list в представление
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mgs_list'] = MGS.objects.all()
        # так же понадобится информация о нитке в которой расположена нода
        switch_id = self.kwargs['pk']
        campus = ACCESS_SWITCH.objects.get(id=switch_id).access_node.thread.campus
        context['campus'] = campus
        return context
    # Если необходимо после смены модели перейти к кампусу то необходимо разкоментировать процедуру get_success_url
    # Поумолчанию после смены модели происходит переход к настройкам коммутатора
    #def get_success_url(self, **kwargs):
    #    view_name = 'campus'
    #    access_switch_id = self.kwargs['pk']
    #
    #    access_switch = ACCESS_SWITCH.objects.get(id=access_switch_id)
    #    campus_id = access_switch.access_node.thread.campus.id
    #    # No need for reverse_lazy here, because it's called inside the method
    #    return reverse(view_name, kwargs={'pk': campus_id})
