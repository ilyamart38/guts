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
from django import forms
from datetime import datetime
from django.utils import timezone

from .forms import Ms_Form, Campus_Form, SubnetInThread_Form, New_Access_Switch_Form, Ports_Of_Acess_Switch_Formset
from . import net_lib

# Класс заглавного представления приложения
class IndexView(LoginRequiredMixin, generic.ListView):
    template_name = 'network/index.html'
    context_object_name = 'mgs_list'

    def get_queryset(self):
        return MGS.objects.order_by('mgs_num')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for mgs in context['object_list']:
            state_age = int(datetime.now().day-mgs.last_update.day)
            #print(mgs, state_age)
            if abs(state_age) > 1:
                mgs.update_counts()
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
        mgs = context['object']
        #for ms in mgs.ms_set.all():
        #    for campus in ms.campus_set.all():
        #        state_age = int(datetime.now().day-campus.last_update.day)
        #        #print(campus, state_age)
        #        if abs(state_age) > 1:
        #            campus.update_counts()
        #        #else:
        #        #    print('OK', datetime.now().hour, campus.last_update.hour)
                    
        return context

# Клас представления для кампуса
class CampusView(LoginRequiredMixin, generic.DetailView):
    model = CAMPUS
    # Для корректного отображения списка МГС влевой части добавляем контекст mgs_list в представление
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mgs_list'] = MGS.objects.all()
        context['object'].update_counts()
        return context

# Клас представления для нитки    
class ThreadView(LoginRequiredMixin, generic.DetailView):
    model = THREAD

# класс для создания нового кампуса в текущей МС
class NewCampusInMs(LoginRequiredMixin, CreateView):
    model = CAMPUS
    fields = ['prefix', 'ms', 'num_in_ms']
    
    # определяем начальные значения формы:
    def get_initial(self):
        ms_id = self.kwargs['ms_id']
        ms = MS.objects.get(id=ms_id)
        # Вычисляем первый свободный номер кампуса
        num_in_ms=1
        while CAMPUS.objects.filter(num_in_ms=num_in_ms, ms = ms):
            num_in_ms += 1
        
        return{
            'ms' : ms_id,
            'num_in_ms' : num_in_ms
        }
    
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['mgs_list'] = MGS.objects.all()
        return context

# Клас представления для изменения настроек кампуса
class CampusUpdate(LoginRequiredMixin, UpdateView):
    model = CAMPUS
    fields = ('prefix', 'ms', 'num_in_ms')

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        campus_id = self.kwargs['pk']
        context['campus'] = CAMPUS.objects.get(id = campus_id)
        context['mgs_list'] = MGS.objects.all()
        return context

# класс для создания новой МС в текущей МГС
class NewMsInMgs(LoginRequiredMixin, CreateView):
    model = MS
    fields = ['mgs', 'num_in_mgs',]
    
    # определяем начальные значения формы:
    def get_initial(self):
        mgs_id = self.kwargs['mgs_id']
        mgs = MGS.objects.get(id = mgs_id)
        # Вычисляем первый свободный номер МС
        num_in_mgs=1
        while MS.objects.filter(mgs=mgs, num_in_mgs=num_in_mgs):
            num_in_mgs += 1
        
        return{
            'mgs' : mgs_id,
            'num_in_mgs' : num_in_mgs
        }
    
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        mgs_id = self.kwargs['mgs_id']
        context['mgs'] = MGS.objects.get(id = mgs_id)
        context['mgs_list'] = MGS.objects.all()
        return context

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
        ms_id = self.kwargs['pk']
        context['ms'] = MS.objects.get(id = ms_id)
        context['mgs_list'] = MGS.objects.all()
        return context

# класс для создания новой нитки в текущем кампусе
class NewThreadInCampus(LoginRequiredMixin, CreateView):
    model = THREAD
    fields = ['campus', 'num_in_campus', 'outvlan', 'mapvlan', ]
    
    # определяем начальные значения формы:
    def get_initial(self):
        campus_id = self.kwargs['campus_id']
        campus = CAMPUS.objects.get(id=campus_id)
        num_in_campus=1
        # Вычисляем номер очередной свободной нитки
        while THREAD.objects.filter(campus=campus, num_in_campus=num_in_campus):
            num_in_campus += 1
        # Пытаемся расчитать внешний и влан для мапинга
        outvlan = net_lib.calculation_outvlan(campus.ms.mgs.mgs_num, campus.ms.num_in_mgs, campus.num_in_ms, num_in_campus)
        mapvlan = net_lib.calculation_mapvlan(campus.ms.num_in_mgs, campus.num_in_ms, num_in_campus)
        # Если outvlan и map влан не удалось найти то подбераем свободные вланы за пределами концепции
        if not outvlan or not mapvlan:
            for calc_ms in (7,8):
                for calc_campus in range(1,9):
                    # исключаем x.7.1-x.7.6
                    if not(calc_ms == 7 and calc_campus in range(1,7)):
                        for calc_thread in range(1,5):
                            calc_outvlan = net_lib.calculation_outvlan(campus.ms.mgs.mgs_num, calc_ms, calc_campus, calc_thread)
                            # Если нет нитки с таким вланом то забераем его
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
        return{
            'campus': campus_id, 
            'num_in_campus': num_in_campus,
            'mapvlan': mapvlan,
            'outvlan': outvlan,
        }
        
    
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['mgs_list'] = MGS.objects.all()
        return context

# Клас представления для изменения настроек нитки
class ThreadUpdate(LoginRequiredMixin, UpdateView):
    model = THREAD
    fields = ('num_in_campus', 'outvlan', 'mapvlan')
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
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mgs_list'] = MGS.objects.all()
        return context

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

# класс для создания нового кампуса в текущей МС
class SubnetInThread(LoginRequiredMixin, CreateView):
    model = SUBNET
    fields = [
        'thread', 
        'network', 
        'gw',
    ]

    def get_form(self):
        form = super(SubnetInThread, self).get_form()
        # Т.к. нитка уже определена, необходимо скрыть поле выбора нитки!
        form.fields['thread'].widget = forms.HiddenInput()
        return form
    
    # определяем начальные значения формы:
    def get_initial(self):
        thread_id = self.kwargs['thread_id']
        thread = THREAD.objects.get(id=thread_id)
        
        thread_num = thread.num_in_campus
        campus_num = thread.campus.num_in_ms
        ms_num = thread.campus.ms.num_in_mgs
        mgs_num = thread.campus.ms.mgs.mgs_num
        network = net_lib.calculation_subnet(mgs_num, ms_num, campus_num, thread_num)
        gw = '0.0.0.0'
        if SUBNET.objects.filter(network=network).count() > 0:
            network = None
            # Если outvlan и map влан не удалось найти то подбераем свободные вланы за пределами концепции
            for calc_ms in (7,8):
                for calc_campus in range(1,9):
                    # исключаем x.7.1-x.7.6
                    if not(calc_ms == 7 and calc_campus in range(1,7)):
                        for calc_thread in range(1,5):
                            network = net_lib.calculation_subnet(mgs_num, calc_ms, calc_campus, calc_thread)
                            if network:
                                break
                    if network:
                        break
                if network:
                    break
        if network:
            net = SUBNET(network=network)
            gw = net.ip_address()[-1]
        return{
            'thread': thread_id,
            'network': network,
            'gw' : gw,
            }
    
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['mgs_list'] = MGS.objects.all()
        context['thread'] = THREAD.objects.get(id=self.kwargs['thread_id'])
        return context

class SubnetDelete(DeleteView):
    model=SUBNET
    
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['mgs_list'] = MGS.objects.all()
        return context
    def delete(self, request, *args, **kwargs):
        subnet_id = self.kwargs['pk']

        subnet = SUBNET.objects.get(id=subnet_id)
        campus_id = subnet.thread.campus.id
        subnet.delete()

        return HttpResponseRedirect(reverse('campus', kwargs={'pk': campus_id}))

# класс для создания нового нового узла в текущей нитке
class NewAccessNodeInThread(LoginRequiredMixin, CreateView):
    model = ACCESS_NODE
    fields = ['address', 'thread',]
    
    # определяем начальные значения формы:
    def get_initial(self):
        thread_id = self.kwargs['thread_id']
        # Вычисляем первый свободный номер кампуса
        
        return{
            'thread' : thread_id,
        }

    def get_form(self):
        form = super(NewAccessNodeInThread, self).get_form()
        # Т.к. нитка уже определена, необходимо скрыть поле выбора нитки!
        form.fields['thread'].widget = forms.HiddenInput()
        return form
    
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['mgs_list'] = MGS.objects.all()
        context['thread'] = THREAD.objects.get(id=self.kwargs['thread_id'])
        return context

# Клас представления для изменения узла доступа
class AccessNodeUpdate(LoginRequiredMixin, UpdateView):
    model = ACCESS_NODE
    fields = ('address',)
    # Для корректного отображения списка МГС влевой части добавляем контекст mgs_list в представление
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mgs_list'] = MGS.objects.all()
        # так же понадобится информация о нитке в которой расположена нода
        node_id = self.kwargs['pk']
        access_node = ACCESS_NODE.objects.get(id=node_id)
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

# класс для создания нового нового коммутатора доступа в текущем узле
class NewAccessSwitchInNode(LoginRequiredMixin, CreateView):
    template_name = 'network/new_access_switch_in_node.html'
    model = ACCESS_SWITCH
    fields = [
        'access_node',
        'stp_root',
        'ip', 
        'mac',
        'sn',
        'sw_model', 
    ]
    
    def get_form(self):
        access_node_id = self.kwargs['access_node_id']
        access_node = ACCESS_NODE.objects.get(id=access_node_id)
        form = super(NewAccessSwitchInNode, self).get_form()
        # Необходимо сформировать список ip-адресов из незанятых в данной нитке
        ip_list=[]
        subnet_list = SUBNET.objects.filter(thread=access_node.thread)
        for subnet in subnet_list:
            for ip in subnet.ip_address():
                if not ACCESS_SWITCH.objects.filter(ip=ip):
                    choice = (str(ip), str(ip))
                    ip_list.append(choice)
        form.fields['ip'].widget = forms.widgets.Select(choices=ip_list)
        # Т.к. нода уже определена, необходимо скрыть поле выбора ноды!
        form.fields['access_node'].widget = forms.HiddenInput()
        return form

    # определяем начальные значения формы:
    def get_initial(self):
        initial = {}
        access_node_id = self.kwargs['access_node_id']
        access_node = ACCESS_NODE.objects.get(id=access_node_id)
        # Если в нитке ни у одного коммутатора не установлен параметр stp_root, необходимо установить этот параметр у создаваемого коммутатора поумолчанию
        if not ACCESS_SWITCH.objects.filter(
                    access_node__in = ACCESS_NODE.objects.filter(
                        thread = access_node.thread
                    ), stp_root = True
                ):
                    print("stp_root - OK")
                    initial['stp_root'] = True
                    
        else:
                    print("stp_root - NE OK")
        initial['access_node'] = access_node_id
        
        return initial
    
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['mgs_list'] = MGS.objects.all()
        context['access_node'] = ACCESS_NODE.objects.get(id=self.kwargs['access_node_id'])
        return context

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
                form_type = int(form['port_type'].value())
                if form_type not in (0, 1):
                    form.save()
                else:
                    id = form['id'].value()
                    if PORT_OF_ACCESS_SWITCH.objects.get(id=id).port_type.id != form_type:
                        print(PORT_OF_ACCESS_SWITCH.objects.get(id=id).port_type.id, form['port_type'].value())
                        form.save()
                    
            ## после сохранения всех настроек на портах, необходимо обновить настройки всех магистральных портов в нитке
            #uplink_ports_in_thread = PORT_OF_ACCESS_SWITCH.objects.filter(
            #    port_type__in = PORT_TYPE.objects.filter(id__in = (0,1)),
            #    access_switch__in = ACCESS_SWITCH.objects.filter(
            #        access_node__in = ACCESS_NODE.objects.filter(thread = ACCESS_SWITCH.objects.get(id = access_switch_id).access_node.thread)
            #    )
            #)
            ##print(uplink_ports_in_thread)
            #for port in uplink_ports_in_thread:
            #    port.save_uplink()
            ##При любых изменениях в настройках коммутатора стираем значение cfg_file, кроме случая когда мы задаем cfg_file
            #access_switch = ACCESS_SWITCH.objects.get(id=access_switch_id)
            #access_switch.cfg_file = ''
            #access_switch.save()
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
            #print('FORM_SET_ERROR_COUNT', form_set.total_error_count())
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
    fields = (
        'stp_root',
        'mac',
        'sn',
        'sw_model',)
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

class AccessSwitchCfgGen(LoginRequiredMixin, generic.DetailView):
    model = ACCESS_SWITCH
    template_name = 'network/access_switch_gen_cfg.html'
   
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mgs_list'] = MGS.objects.all()
        return context

