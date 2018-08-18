from django.db import models
from clients.models import CLIENTS
from guts.settings import CONNECTION_TYPES
from guts.settings import GUTS_CONSTANTS
from guts.settings import MEDIA_ROOT
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.core.files import File
import SubnetTree
import ipaddress
import re
import os
#from datetime import datetime
from django.utils import timezone
from . import net_lib

# Валидатор корректности записи подсети IPv4 (0-255).(0-255).(0-255).(0-255)/(0-32)
def validator_net_addr(network):
    # проверяем, является ли переданное значение адресом подсети
    try:
        current_network = ipaddress.ip_network(network)
        #Разрешаем использовать сети не короче /30
        if current_network.prefixlen > 30:
            raise ValidationError('Для сети не разрешено использовать префикс больше 30!')
    except ValueError:
        raise ValidationError('Введенные данные не могут являться адресом подсети!')

# валидатор для проверки подсетей добавляемых в нитки ГУТС
# сеть проверяется на предмет пересечения с сетями уже используемыми на уровне доступа
def validator_subnet(subnet):
    network = subnet.network
    current_network = ipaddress.ip_network(network)
    # проверяем можноли использовать введенные данные на нашей сети
    current_net_in_guts = False
    for net in GUTS_NETWORK.objects.all():
        guts_network = ipaddress.ip_network(net.network)
        if current_network.network_address in guts_network:
            current_net_in_guts = True
            break
    if not current_net_in_guts:
        raise ValidationError("Адрес не принадлежит адресам разрешенным в ГУТС города!")
    
    # проверяем не используются ли введенные данные в какой-либо нитке
    # Перебираем в каждой нитке
    for thread in THREAD.objects.all():
        # каждую подсеть
        for subnet_exmpl in thread.subnet_set.all():
            thread_net = ipaddress.ip_network(subnet_exmpl.network)
            # если введенные данные уже где-то используются то говорим "Ай-ай-ай!!!"
            # также говорим "Ай-ай-ай!!!" если подсеть в какой-либо нитке входит в веденную сеть
            # исключая только саму редактируемую нитку
            if subnet_exmpl != subnet:
                if current_network.network_address in thread_net or ipaddress.ip_network(subnet_exmpl.network).network_address in current_network:
                    raise ValidationError("Указанный адрес сети не может использоваться т.к. пересекается с %s (%s)!" % (thread, subnet.network))

def validator_vid(vid):
    if vid < 0:
        raise ValidationError("Значение VID (%s) не может быть меньше нуля!" % vid)
    if vid > 4094:
        raise ValidationError("Значение VID (%s) не может быть больше 4094!" % vid)

# Класс описывающий сети разрешонные в ГУТС города
class GUTS_NETWORK(models.Model):
    class Meta:
        verbose_name = "Подсеть"
        verbose_name_plural = "Подсети разрешонные в ГУТС."
        ordering = ['description',]

    network = models.CharField(max_length = 18, unique=True, validators=[validator_net_addr, ])
    description = models.CharField(max_length = 100)
    
    def __str__(self):
        return "%s (%s)" % (self.network, self.description)

# Класс описывающий lag в сторону уровня агрегации
class LAG(models.Model):
    title = models.IntegerField(default = 0)
    
    def __str__(self):
        return "lag-%s" % self.title

# Класс описывающий sap
class SAP(models.Model):
    class Meta:
        unique_together = ('lag', 's_vlan', 'c_vlan',)
        ordering = ['lag', 's_vlan', 'c_vlan']

    title = models.CharField(max_length=100)
    lag = models.ForeignKey(LAG, on_delete = models.SET_NULL, blank=True, null=True)
    s_vlan = models.IntegerField(default=1, verbose_name='SVID', validators=[validator_vid, ])
    c_vlan = models.IntegerField(default=1, verbose_name='CVID', validators=[validator_vid, ])
    
    def __str__(self):
        return "%s:%s.%s (%s)" % (self.lag, self.s_vlan, self.c_vlan, self.title)
    
# Класс описывающий объект МГС
class MGS(models.Model):
    class Meta:
        verbose_name = "МГС"
        verbose_name_plural = "МГС"

    mgs_num = models.IntegerField(default=0, unique=True)
    # Адрес МГС
    address = models.CharField(max_length = 100)
    lag = models.ForeignKey(LAG, on_delete = models.SET_NULL, blank=True, null=True)
    # отдельные поля для хранения информации о количестве кампусов/узлов/коммутаторов, 
    # которые будут обновляться раз в сутки, для этого еще поле с временем последнего обновления
    campus_counter = models.IntegerField(default = 0, verbose_name="Количество кампусов в МГС", help_text = "Значение обновляется автоматически при вызове метода update_counts()") #,         editable=False)
    node_counter = models.IntegerField(default = 0, verbose_name="Количество узлов в МГС", help_text = "Значение обновляется автоматически при вызове метода update_counts()") #,              editable=False)
    switche_counter = models.IntegerField(default = 0, verbose_name="Количество коммутаторов в МГС", help_text = "Значение обновляется автоматически при вызове метода update_counts()") #,    editable=False)
    last_update = models.DateTimeField(default=timezone.now, verbose_name='Время последнего обновления данных по МГС',                                                                                            editable=False)
    # Представление МГС
    def __str__(self):
        return "МГС-%s" % self.mgs_num

    # Процедура обновления счетчиков по МГС
    def update_counts(self):
        campuss_count = 0
        node_count = 0
        sw_count = 0
        for ms in self.ms_set.all():
            campuss_count += ms.campus_set.count()
            for campus in ms.campus_set.all():
                for thread in campus.thread_set.all():
                    node_count += thread.access_node_set.count()
                    for node in thread.access_node_set.all():
                        sw_count += node.access_switch_set.count()
                        
        self.campus_counter = campuss_count
        self.node_counter = node_count
        self.switche_counter = sw_count
        self.last_update = timezone.now()
        self.save()
    

# Класс описывающая объект магистрали
class MS(models.Model):
    class Meta:
        verbose_name = "Магистраль"
        verbose_name_plural = "Магистрали"
        unique_together = ('mgs', 'num_in_mgs',)
    
    mgs = models.ForeignKey(MGS, on_delete = models.CASCADE, verbose_name="МГС")
    # номер магистрали должен быть уникальным впределах МГС
    num_in_mgs = models.IntegerField(default = 1, verbose_name="Номер магистрали в МГС")
    
    def __str__(self):
        return "МС-%s.%s" % (self.mgs.mgs_num, self.num_in_mgs)

    def get_absolute_url(self):
        from django.urls import reverse
        
        return reverse('mgs', args=[str(self.mgs.id)])
        
# Класс описывающий объект кампуса (ППК/МКУ)
class CAMPUS(models.Model):
    class Meta:
        verbose_name = "Кампус"
        verbose_name_plural = "Кампусы"
        ordering = ('ms', 'num_in_ms')
        unique_together = ('ms', 'num_in_ms',)

    prefix_choices = (
        ('ppk', 'ППК'),
        ('mku', 'МКУ'),
    )
    # Префикс названия (ППК-1.1.1, МКУ-8.2.1)
    prefix = models.CharField(max_length = 20,
        default = 'ppk',
        choices = prefix_choices,
        verbose_name='Префикс')
    # Принадлежность к МС
    ms = models.ForeignKey(MS, on_delete=models.CASCADE, verbose_name='МС')
    num_in_ms = models.IntegerField(default = 1)
    # отдельные поля для хранения информации о узлов/коммутаторов, 
    # которые будут обновляться раз в сутки, для этого еще поле с временем последнего обновления
    node_counter = models.IntegerField(default = 0, verbose_name="Количество узлов в кампусе", help_text = "Значение обновляется автоматически при вызове метода update_counts()",              editable=False)
    switche_counter = models.IntegerField(default = 0, verbose_name="Количество коммутаторов в кампусе", help_text = "Значение обновляется автоматически при вызове метода update_counts()",    editable=False)
    last_update = models.DateTimeField(default=timezone.now, verbose_name='Время последнего обновления данных по МГС',                                                                          )#editable=False)
    
    # Представление кампуса
    def __str__(self):
        return "%s-%s.%s.%s" % (self.get_prefix_display(), self.ms.mgs.mgs_num, self.ms.num_in_mgs, self.num_in_ms)
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('campus', args=[str(self.id)])
    
    # Процедура обновления счетчиков по МГС
    def update_counts(self):
        print('update %s' % self)
        node_count = 0
        sw_count = 0
        for thread in self.thread_set.all():
            node_count += thread.access_node_set.count()
            for node in thread.access_node_set.all():
                sw_count += node.access_switch_set.count()
        self.node_counter = node_count
        self.switche_counter = sw_count
        print('>', self.last_update)
        self.last_update = timezone.now()
        print('>>', self.last_update)
        self.save()
        
    def save(self, *args, **kwargs):
        # Если происходит создание нового кампуса, то сразу после сохранения, создаем нитки в созданом кампусе, 
        if CAMPUS.objects.filter(id=self.id).count() == 0:
            super(CAMPUS, self).save(*args, **kwargs)
            # если создается новый кампус и это ППК, то сразу в ППК создаем четыре нитки
            # если создается МКУ, то добавляем только одну нитку
            if self.prefix == 'ppk':
                threads_count = 4
            elif self.prefix == 'mku':
                threads_count = 1
            for num_in_campus in range(1,threads_count+1):
                thread = THREAD(campus=self, num_in_campus=num_in_campus)
                outvlan = net_lib.calculation_outvlan(self.ms.mgs.mgs_num, self.ms.num_in_mgs, self.num_in_ms, num_in_campus)
                if outvlan:
                    thread.outvlan = outvlan
                mapvlan = net_lib.calculation_mapvlan(self.ms.num_in_mgs, self.num_in_ms, num_in_campus)
                if mapvlan:
                    thread.mapvlan = mapvlan
                thread.save()
            # Иначе просто сохраняем изменения
        else:
            super(CAMPUS, self).save(*args, **kwargs)

# Класс описывающий нитку, соответствующую одному l2-сегменту в пределах МГС
class THREAD(models.Model):
    class Meta:
        verbose_name = "Нитка"
        verbose_name_plural = "Нитки"
        unique_together = ('campus', 'num_in_campus',)
        ordering = ['campus', 'num_in_campus']

    # Название нитки (1.1.1-1, 8.2.1-1)
    #title = models.CharField(max_length = 20)
    campus = models.ForeignKey(CAMPUS, on_delete = models.CASCADE)
    num_in_campus = models.IntegerField(default = 1)
    outvlan = models.IntegerField(default=1, verbose_name='Внешний vlan', validators=[validator_vid, ])
    mapvlan = models.IntegerField(default=1, verbose_name='Map-vlan', validators=[validator_vid, ])

    def save(self, *args, **kwargs):
        # Если происходит создание новой нитки, то сразу после сохранения нитки, создаем подсеть для нитки, 
        # если номера мгс/мс/кампуса/нитки соответствуют концепции, и если расчитаная подсеть еще не занята
        if THREAD.objects.filter(id=self.id).count() == 0:
            super(THREAD, self).save(*args, **kwargs)
            
            thread_num = self.num_in_campus
            campus_num = self.campus.num_in_ms
            ms_num = self.campus.ms.num_in_mgs
            mgs_num = self.campus.ms.mgs.mgs_num
            network = net_lib.calculation_subnet(mgs_num, ms_num, campus_num, thread_num)
            if network:
                if SUBNET.objects.filter(network=network).count() == 0:
                    subnet = SUBNET(network=network, thread=self)
                    subnet.save()
                else:
                    print('Подсеть %s уже занята!' % network)
            else:
                print('Нитка %s.%s.%s-%s не соответствует концепции!' % (mgs_num, ms_num, campus_num, thread_num))
        # Иначе просто сохраняем изменения
        else:
            super(THREAD, self).save(*args, **kwargs)
        
    # Представление нитки
    def __str__(self):
        return "%s-%s" % (self.campus, self.num_in_campus)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('campus', args=[str(self.campus.id)])
    
    # Процедура определения списка вланов используемого в нитке
    def used_vlans(self):
        used_vlans = {}
        
        # список клиентских портов на всех коммутаторах в нитке:
        ports_in_thread = PORT_OF_ACCESS_SWITCH.objects.filter(
                                                        access_switch__in = ACCESS_SWITCH.objects.filter(
                                                                                                  access_node__in =  ACCESS_NODE.objects.filter(thread = self)
                                                                                                  ),
                                                        port_type__in = PORT_TYPE.objects.filter(
                                                                                          connection_type__in = [3,4]
                                                                                          )
                                                        )
        # перебераем каждый порт
        for port in ports_in_thread:
            ## изучаем вланы на всех портах кроме аплинков и распред.портов!
            #if port.port_type.id not in (0, 1):
                # запоминаем u_vlan влан
                if port.u_vlan != 0:
                    if port.u_vlan not in used_vlans:
                        used_vlans[port.u_vlan] = {}
                        used_vlans[port.u_vlan]['used_in'] = []
                    used_vlans[port.u_vlan]['used_in'].append(" %s [%s]" % (port.access_switch, port.port_name))
                # тоже самое делаем для всех t_vlan
                for t_vlan in net_lib.interval_to_arr(port.t_vlans):
                    # запоминаем t_vlan влан
                    if t_vlan != 0:
                        if t_vlan not in used_vlans:
                            used_vlans[t_vlan] = {}
                            used_vlans[t_vlan]['used_in'] = []
                        used_vlans[t_vlan]['used_in'].append(" %s [%s]" % (port.access_switch, port.port_name))
        #print('>>>>>>>>>>', used_vlans)
        #print(net_lib.arr_to_interval(used_vlans.keys()))
        return used_vlans

    def ip_address(self):
        list_ip = []
        for subnet in SUBNET.objects.filter(thread=self):
            list_ip += subnet.ip_address()
        return list_ip
    
    def free_ip_address(self):
        list_ip = []
        for ip in self.ip_address():
            #print('>>>',ip)
            if ACCESS_SWITCH.objects.filter(
                    access_node__in=ACCESS_NODE.objects.filter(
                        thread = self,
                    ),
                    ip = ip,
                ).count() == 0:
                list_ip.append(ip)
        return list_ip
            
# Класс описывающий подсеть устройств
class SUBNET(models.Model):
    class Meta:
        verbose_name = "Подсеть"
        verbose_name_plural = "Подсети"
    
    #Нитка в которой используется данная подсеть
    thread = models.ForeignKey(THREAD, on_delete=models.CASCADE, verbose_name='Нитка')
    # адрес сети
    network = models.CharField(max_length = 18, unique = True, verbose_name='Подсеть')
    gw = models.GenericIPAddressField(protocol = 'IPv4', default='0.0.0.0', verbose_name='Адрес шлюза')

    # Представление подсети
    def __str__(self):
        return "%s" % (self.network)
    
    # функция для определения принадлежности ip-адреса подсети описанной объектом
    def __contains__(self, ip):
        if ip in self.ip_address():
            return True
        else:
            return False
    
    def clean(self):
        validator_net_addr(self.network)
        validator_subnet(self)
    
    def ip_address(self):
        list_ip=[]
        ip_net = ipaddress.ip_network(self.network)
        for ip in ip_net:
            if ip not in (ip_net.network_address, ip_net.broadcast_address, ipaddress.ip_address(self.gw)):
                list_ip.append(ip.compressed)
        return list_ip
    def gw_address(self):
        ip_net = ipaddress.ip_network(self.network)
        ip = ip_net.broadcast_address-1
        return ip.compressed
    
    def hosts_count(self):
        return self.ip_address().count
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('campus', args=[str(self.thread.campus.id)])

    def save(self, *args, **kwargs):
        # При сохранении проверяем задано ли значение шлюза
        # если не задано то указываем последний адрес подсети
        if self.gw == '0.0.0.0':
            self.gw = self.gw_address()
        super(SUBNET, self).save(*args, **kwargs)
    
# Класс описывающий производителей оборудования
class VENDORS(models.Model):
    class Meta:
        verbose_name = "Вендор"
        verbose_name_plural = "Вендоры"
    
    title = models.CharField(max_length = 100)
    
    def __str__(self):
        return self.title

# Класс описывающий типы портов используемые на коммутаторах
class PORT_TYPE(models.Model):
    class Meta:
        verbose_name = "Тип порта"
        verbose_name_plural = "Типы портов"
        ordering = ['id']

    id = models.IntegerField(primary_key=True)
    title = models.CharField(max_length = 200, blank = True, verbose_name = 'Описание типа порта')
    default_description = models.CharField(max_length = 200, blank = True, verbose_name = 'Название порта поумолчанию')
    color = models.CharField(max_length=7, blank = True, verbose_name='Цвет типа порта.')
    connection_type = models.IntegerField(default = 0, verbose_name = 'Тип подключения.', choices = CONNECTION_TYPES)
    # non_pppoe = models.BooleanField(default=False)
    # is_signal = models.BooleanField(default=False)
    # is_upstream = models.BooleanField(default=False)
    # is_bad = models.BooleanField(default=False)
    
    def __str__(self):
        return '%s-%s' % (self.id, self.title)

def create_help_text_for_type_ports():
    list_help_text = []
    for type_port in PORT_TYPE.objects.all():
        list_help_text.append('%s-%s' % (type_port.id, type_port.title))
    return ', '.join(list_help_text)

# Класс описывающий модель коммутатора
class SW_MODEL(models.Model):
    class Meta:
        verbose_name = "Модель коммутаторов"
        verbose_name_plural = "Модели коммутаторов"
        ordering = ['vendor', 'title']

    vendor = models.ForeignKey(VENDORS, on_delete = models.SET_NULL, blank=True, null=True, verbose_name = 'Производитель')
    title = models.CharField(max_length = 100, verbose_name = 'Название модели')
    eqm_type = models.CharField(max_length = 100, default = '', verbose_name = 'Тип объекта в eqm')
    fw_version = models.CharField(max_length = 100, blank = True, verbose_name = 'Рекомендованная версия ПО')
    fw_file = models.CharField(max_length = 100, blank = True, verbose_name = 'Файл прошивки')
    fw_update_commands = models.TextField(blank = True, verbose_name = 'Описание процесса обновления прошивки')
    hw_version = models.CharField(max_length = 100, blank = True, verbose_name = 'HW версия')
    ports_count = models.IntegerField(default = 0, verbose_name = 'Количество портов')
    ports_names = models.CharField(max_length = 500, blank = True, verbose_name = 'Названия портов в конфиге')
    ports_types = models.CharField(max_length = 200, blank = True, verbose_name = 'Типы портов по умолчанию', help_text = create_help_text_for_type_ports())
    #cfg_template = models.CharField(max_length = 100, blank = True)
    cfg_template = models.FileField(upload_to = 'cfg_templates')
    
    cfg_download_commands = models.TextField(blank = True, verbose_name = 'Описание процесса загрузки конфигурации')
    # Представление модели коммутатора
    def __str__(self):
        return "%s %s" % (self.vendor, self.title)
    
    def clean(self):
        if len(self.ports_types.split(',')) != self.ports_count:
            raise ValidationError('Настройки типов портов не соответствуют введенному количеству портов! (%s != %s)' % (len(self.ports_types.split(',')), self.ports_count))
        if len(self.ports_names.split(',')) != self.ports_count:
            raise ValidationError('Настройки названий портов не соответствуют введенному количеству портов! (%s != %s)' % (len(self.ports_names.split(',')), self.ports_count))
        for port_type in self.ports_types.split(','):
            #print(port_type, PORT_TYPE.objects.filter(id=port_type), PORT_TYPE.objects.filter(id=port_type).count())
            if PORT_TYPE.objects.filter(id=port_type).count() == 0:
                raise ValidationError('Введен неопределенный тип порта! (%s)' % port_type)

    def fw_update(self):
        update_text = ''
        if self.fw_update_commands:
            for line in self.fw_update_commands.split('\r'):
                if line.find('<TFTP_IP>') >= 0:
                    tftp_ip_local = "<b>%s</b>" % GUTS_CONSTANTS['TFTP_IP_LOCAL']
                    update_text += (re.sub('<TFTP_IP>', tftp_ip_local, line))
                    tftp_ip_remote = "<b>%s</b>" % GUTS_CONSTANTS['TFTP_IP_REMOTE']
                    update_text += (re.sub('<TFTP_IP>', tftp_ip_remote, line))
                else:
                    update_text += (line)
            fw_version = "<b>%s</b>" % self.fw_version
            update_text = re.sub("<FW>", fw_version, update_text)
            update_text = re.sub("<FW_FILE>", self.fw_file, update_text)
        else:
            update_text = 'Для данной модели коммутатора нет описания процесса обновления прошивки!'
        return update_text
# Класс описывающий узел уровня доступа
class ACCESS_NODE(models.Model):
    class Meta:
        verbose_name = "Узел доступа"
        verbose_name_plural = "Узлы доступа"
        unique_together = ('address', 'thread',)
    
    address = models.CharField(max_length = 100)
    thread = models.ForeignKey(THREAD, on_delete = models.CASCADE)

    # Представление узла
    def __str__(self):
        return "%s (%s)" % (self.address, self.thread)
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('campus', args=[str(self.thread.campus.id)])

# Класс описывающий коммутатор уровня доступа
class ACCESS_SWITCH(models.Model):
    class Meta:
        verbose_name = "Коммутатор доступа"
        verbose_name_plural = "Коммутаторы доступа"
    
    access_node = models.ForeignKey(ACCESS_NODE, on_delete = models.CASCADE)
    sw_model = models.ForeignKey(SW_MODEL, on_delete = models.SET_NULL, blank=True, null=True)
    ip = models.GenericIPAddressField(protocol = 'IPv4', unique=True)
    network = models.ForeignKey(SUBNET, on_delete = models.SET_NULL, blank=True, null=True, editable=False)
    stp_root = models.BooleanField(default=False, verbose_name = 'STP_ROOT')
    #cfg_file = models.CharField(max_length = 200, blank = True, verbose_name = 'Файл текущей конфигурации.', help_text = 'Значение поля очищается при каждых изменениях коммутатора')
    cfg_file = models.FileField(upload_to = 'cfg_switches')
    
    def clean(self):
        # В зависимости от того создается новый коммутатор или обновляется существующий
        # процедура валидации ip-адреса разная
        ip_list = self.access_node.thread.free_ip_address()
        if ACCESS_SWITCH.objects.filter(id=self.id).count() > 0:
            cur_sw = ACCESS_SWITCH.objects.get(id=self.id)
            ip_list.append(cur_sw.ip)
        if self.ip not in ip_list:
            raise ValidationError('Ip-адрес коммутатора (%s), должна пренадлежать подсетям из нитки (%s) которой он пренадлежит!' % (self.ip, self.access_node.thread))
            
    # Представление коммутатора доступа
    def __str__(self):
        address = self.access_node.address
        ip = self.ip
        return "%s (%s)" % (address, ip)

    def save(self, *args, **kwargs):
        # если происходит обновление данных существующего коммутатора
        if ACCESS_SWITCH.objects.filter(id = self.id):
            curr_sw = ACCESS_SWITCH.objects.get(id = self.id)
            # Если задана модель коммутатора
            if self.sw_model and curr_sw.sw_model != self.sw_model:
                # делаем выборку по портам коммутатора
                ports = PORT_OF_ACCESS_SWITCH.objects.filter(access_switch=self)
                # если портов стало больше то добавленные порты настраиваем в соответствии с шаблоном модели
                # а настройки старых портов не меняем
                for port_num in range(1, self.sw_model.ports_count+1):
                    # если порт старый, то не трогаем его
                    # если порт новый создаем новый порт и выставляем настройки в соответствии с моделью
                    if ports.filter(num_in_switch=port_num).count() == 0:
                        self.port_of_access_switch_set.create(
                            num_in_switch = port_num,
                        )
                    # Если порт старый был/стал аплинком или портом расширения, то меняем настройки в соответствии с новой моделью
                    elif ports.get(num_in_switch=port_num).port_type.id in (0, 1) or PORT_TYPE.objects.get(id=self.sw_model.ports_types.split(',')[port_num-1]).id in (0, 1):
                        # Меняем настройки порта port_num
                        #print ('Меняем настройки порта', port_num, PORT_TYPE.objects.get(id=self.sw_model.ports_types.split(',')[port_num-1]))
                        edit_port = ports.get(num_in_switch=port_num)
                        edit_port.port_type =  PORT_TYPE.objects.get(id=self.sw_model.ports_types.split(',')[port_num-1])
                        edit_port.description = PORT_TYPE.objects.get(id=self.sw_model.ports_types.split(',')[port_num-1]).default_description
                        edit_port.default_u_vlan()
                        edit_port.port_name = self.sw_model.ports_names.split(',')[port_num-1]
                        edit_port.save()
                    else:
                        edit_port = ports.get(num_in_switch=port_num)
                        #print('БЕЗ ИЗМЕНЕНИЙ!', ports.get(num_in_switch=port_num), 'type =',ports.get(num_in_switch=port_num).port_type.id, ') / ', PORT_TYPE.objects.get(id=self.sw_model.ports_types.split(',')[port_num-1]))
                        edit_port.port_name = self.sw_model.ports_names.split(',')[port_num-1]
                        #print(self.sw_model.ports_names.split(',')[port_num-1])
                        edit_port.save()
                # в случае если портов стало меньше, удаляем старые порты
                for port in ports:
                    if port.num_in_switch not in range(1, self.sw_model.ports_count+1):
                        #print('Удаление порта', port.num_in_switch)
                        port.delete()
            super(ACCESS_SWITCH, self).save(*args, **kwargs)
        # если происходит добавление нового коммутатора
        else:
            for net in SUBNET.objects.all():
                if self.ip in net:
                    self.network = net
                    break
            super(ACCESS_SWITCH, self).save(*args, **kwargs)
            if self.sw_model:
                for port_num in range(1, self.sw_model.ports_count+1):
                    self.port_of_access_switch_set.create(
                        num_in_switch = port_num,
                        port_name = self.sw_model.ports_names.split(',')[port_num-1]
                        )
        if not self.network or self.ip not in self.network:
            print('???NET???')
            for net in SUBNET.objects.all():
                if self.ip in net:
                    self.network = net
                    break
            super(ACCESS_SWITCH, self).save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('access_switch', args=[str(self.id)])   

    def cfg_download(self):
        download_text = ''
        print('start cfg')
        if self.sw_model.cfg_download_commands:
            # если файл конфигурации не генерировался после последних изменений, то его необходимо сгенерировать
            #if self.cfg_file == '':
            self.cfg_gen()
            if self.cfg_file:
                download_text = "Конфигурация коммутатора записана в файл <a href='%s'>%s</a>\n\r" % (self.cfg_file.url, self.cfg_file.name)
                for line in self.sw_model.cfg_download_commands.split('\r'):
                    if line.find('<TFTP_IP>') >= 0:
                        tftp_ip_local = "<b>%s</b>" % GUTS_CONSTANTS['TFTP_IP_LOCAL']
                        download_text += (re.sub('<TFTP_IP>', tftp_ip_local, line))
                        tftp_ip_remote = "<b>%s</b>" % GUTS_CONSTANTS['TFTP_IP_REMOTE']
                        download_text += (re.sub('<TFTP_IP>', tftp_ip_remote, line))
                    else:
                        download_text += (line)
                download_text = re.sub("<CFG_FILE>", self.cfg_file.name, download_text)
        else:
            download_text = 'Для данной модели коммутатора нет описания процесса загрузки файла конфигурации!'
        return download_text
    
    def cfg_gen(self):
        if self.sw_model.vendor.title == 'D-Link':
            dlink_cfg(self)
            return
        print('>>>>>',self.sw_model.vendor.title)
        

    def gw(self):
        gw_ip = None
        for subnet in SUBNET.objects.filter(thread = self.access_node.thread):
            if self.ip in subnet:
                gw_ip = subnet.gw
                break
        return gw_ip

    def ports(self):
        return range(1,self.sw_model.ports_count+1)
    
    #<CLIENTS_PORTS>        порты с клиентскими подключениями (все кроме бэкбонов, и сигнальных)
    def clients_ports(self):
        return self.port_of_access_switch_set.exclude(
                            port_type__in=PORT_TYPE.objects.filter(
                                    connection_type__in=[0,1,5,99]
                                    )
                            )
        
    #<PPPOE_PORTS>          порты pppoe-клиентов
    def pppoe_ports(self):
        return self.port_of_access_switch_set.filter(
                            port_type__in=PORT_TYPE.objects.filter(
                                    connection_type = 3
                                    )
                            )
    
    #<IP_PORTS>             порты на которых разрешен ip-трафик (не pppoe)
    def ip_ports(self):
        return self.port_of_access_switch_set.filter(
                            port_type__in=PORT_TYPE.objects.filter(
                                    connection_type__in = [0, 1, 4]
                                    )
                            )

    #<BACKBON_PORTS>        порты аплинки+порты расширения
    def backbon_ports(self):
        return self.port_of_access_switch_set.filter(
                            port_type__in=PORT_TYPE.objects.filter(
                                    connection_type__in = [0, 1]
                                    )
                            )
    
    #<NOT_BACKBON_PORTS>    порты кроме аплинков и портов расширения
    def not_backbon_ports(self):
        return self.port_of_access_switch_set.exclude(
                            port_type__in=PORT_TYPE.objects.filter(
                                    connection_type__in = [0, 1]
                                    )
                            )

    #uplink_ports
    def uplink_ports(self):
        return self.port_of_access_switch_set.exclude(
                            port_type__in=PORT_TYPE.objects.filter(
                                    connection_type = 0
                                    )
                            )

    #downlink_ports
    def downlink_ports(self):
        return self.port_of_access_switch_set.exclude(
                            port_type__in=PORT_TYPE.objects.filter(
                                    connection_type__in = [1,3,4]
                                    )
                            )

    #gag_ports (порты для сигнализаторов и неисправные порты)
    def gag_ports(self):
        return self.port_of_access_switch_set.exclude(
                            port_type__in=PORT_TYPE.objects.filter(
                                    connection_type__in = [5, 99]
                                    )
                            )

    def used_vlans(self):
        used_vlans = {}
        
        # перебераем каждый порт
        for port in self.port_of_access_switch_set.all():
            # запоминаем u_vlan влан
            if port.u_vlan != 0:
                if port.u_vlan not in used_vlans:
                    used_vlans[port.u_vlan] = {}
                    used_vlans[port.u_vlan]['used_in'] = []
                used_vlans[port.u_vlan]['used_in'].append(port)
            # тоже самое делаем для всех t_vlan
            for t_vlan in net_lib.interval_to_arr(port.t_vlans):
                # запоминаем t_vlan влан
                if t_vlan != 0:
                    if t_vlan not in used_vlans:
                        used_vlans[t_vlan] = {}
                        used_vlans[t_vlan]['used_in'] = []
                    used_vlans[t_vlan]['used_in'].append(port)
        return used_vlans

# Класс описывающий конечный порт коммутатора доступа
class PORT_OF_ACCESS_SWITCH(models.Model):
    class Meta:
        verbose_name = "Порт коммутатора доступа"
        verbose_name_plural = "Порты коммутаторов доступа"
        ordering = ['access_switch', 'num_in_switch']
        unique_together = ('access_switch', 'num_in_switch', )
        
    access_switch = models.ForeignKey(ACCESS_SWITCH, on_delete = models.CASCADE)
    num_in_switch = models.IntegerField(default = 0)
    description = models.CharField(max_length = 100)
    port_name = models.CharField(max_length = 100)
    port_type = models.ForeignKey(PORT_TYPE, on_delete = models.SET_NULL, blank=True, null=True)
    
    u_vlan = models.IntegerField(default = 0, verbose_name = 'Untag-vlan/PVID')
    t_vlans = models.CharField(max_length = 1000, blank =True)
    def __str__(self):
        return '%s (%s)' % (self.access_switch, self.num_in_switch)
        
    def clean(self):
        if self.u_vlan < 0:
            raise ValidationError('Значение Untag-vlan не может быть отрицательным!!!')
        if self.u_vlan > 4094:
            raise ValidationError('Значение Untag-vlan не может быть большим чем 4094!!!')

    def save(self, *args, **kwargs):
        # Если происходит создание нового порта, то просто выставляем все значения в соответствии с данными модели коммутатора
        if PORT_OF_ACCESS_SWITCH.objects.filter(id=self.id).count() == 0:
            type_id = int(self.access_switch.sw_model.ports_types.split(',')[self.num_in_switch-1])
            self.description = PORT_TYPE.objects.get(id=type_id).default_description
            self.port_type = PORT_TYPE.objects.get(id=type_id)
            self.port_name = self.access_switch.sw_model.ports_names.split(',')[self.num_in_switch-1]
            #вычисляем для порта untag-влан, если это требуеся
            self.default_u_vlan()
            # только для аплинков и распределительных портов 
            if self.port_type.id in (0, 1):
                # то меняем значение u_vlan на 1, а t_vlans на список вланов в нитке, к которой относится коммутатор + permanent_vlans
                self.description = self.port_type.default_description
                self.default_u_vlan()
                # а значение t_vlans на список всех используемых в нитке вланов
                vlans_in_thread = self.access_switch.access_node.thread.used_vlans()
                vlans = vlans_in_thread.keys()
                t_vlans=list(vlans)
                #print(t_vlans)
                t_vlans += net_lib.interval_to_arr(GUTS_CONSTANTS['PERMANENT_VLANS'])
                print(self, t_vlans)
                self.t_vlans = net_lib.arr_to_interval(t_vlans)
            super(PORT_OF_ACCESS_SWITCH, self).save(*args, **kwargs)
        
        # если происходит изменение настроек сущеcтвующего порта то следуем определенным правилам
        else:
            # порт до изменений
            current_port = PORT_OF_ACCESS_SWITCH.objects.get(id=self.id)
            # Если что-то поменялось в порту, то затираем информацию о файле конфигурации коммутатора, 
            # что говорит о том что при необходимости требуется повторно генерировать конфиг
            need_update = False         # переменная по которой мы определяем необходимость обновления аплинков
            # 1. проверяем изменился ли тип порта
            if self.port_type != current_port.port_type:
                print('>>>',current_port.port_type,'->',self.port_type )
                # Если новое значение соответствует магистральному или распределительному порту
                if self.port_type.connection_type in (0, 1):
                    # то меняем значение u_vlan на 1, а t_vlans на список вланов в нитке, к которой относится коммутатор
                    self.description = self.port_type.default_description
                    self.default_u_vlan()
                    # а значение t_vlans на список всех используемых в нитке вланов
                    vlans_in_thread = self.access_switch.access_node.thread.used_vlans()
                    vlans = vlans_in_thread.keys()
                    t_vlans=list(vlans)
                    t_vlans += net_lib.interval_to_arr(GUTS_CONSTANTS['PERMANENT_VLANS'])
                    self.t_vlans = net_lib.arr_to_interval(t_vlans)
                    need_update = True
                # Если новое значение соответствует клиентскому pppoe-порту
                elif self.port_type.connection_type == 3:
                    # В любом случае убираем все тегированные вланы с порта
                    self.t_vlans = ''
                    # Если не изменили описание порта, то выставляем значение поумолчению
                    if self.description == current_port.description:
                        self.description = self.port_type.default_description
                    # Если не изменился клиентский влан, то выставляем влан поумолчанию
                    if self.u_vlan == current_port.u_vlan:
                        self.default_u_vlan()
                # Если новое значение соответствует прочему клиентскому (не pppoe) порту
                elif self.port_type.connection_type == 4:
                    # Если не изменили описание порта, то выставляем значение поумолчению
                    if self.description == current_port.description:
                        self.description = self.port_type.default_description
                    # Значение вланов оставляем без изменений, кроме случая когда до изменений порт являлся аплинком
                    if current_port.port_type.connection_type in [0, 1]:
                        self.u_vlan = 0
                        self.t_vlans = ''
                # Если новое значение соответствует порту какого-либо сигнализатора, или неисправного порта
                elif self.port_type.id in (5,99):
                    # Если не изменили описание порта, то выставляем значение поумолчению
                    if self.description == current_port.description:
                        self.description = self.port_type.default_description
                    # Убираем все вланы с портов
                    self.u_vlan = 0
                    self.t_vlans = ''
            #2. если изменились настройки вланов то необходимо обновить настройки всех магистральных портов в нитке
            if self.port_type.connection_type in (3,4):
                if self.u_vlan != current_port.u_vlan or self.t_vlans != current_port.t_vlans:
                    print('Chenge vlan ', self)
                    # обновление магистральных портов потребуется только в случае появления нового влана
                    port_vlans = []
                    port_t_vlans = net_lib.interval_to_arr(self.t_vlans)
                    if port_t_vlans:
                        port_vlans += port_t_vlans
                    port_vlans.append(self.u_vlan)
                    vlans_in_thread = self.access_switch.access_node.thread.used_vlans()
                    PERMANENT_VLANS = net_lib.interval_to_arr(GUTS_CONSTANTS['PERMANENT_VLANS'])
                    for vlan in port_vlans:
                        print('>>', vlan)
                        if vlan != 0:
                            if vlan not in vlans_in_thread:
                                if vlan not in PERMANENT_VLANS:
                                    print('not in permanent')
                                    # если нашли хотя бы один новы влан то решаемся обновлять аплинки
                                    print('%s not in thread_vlans' % vlan)
                                    need_update = True
                                    break
                            else:
                                print(vlans_in_thread)
            
            super(PORT_OF_ACCESS_SWITCH, self).save(*args, **kwargs)
            
            if need_update:
                    # выбераем все магистральные порты в нитке
                    uplink_ports_in_thread = PORT_OF_ACCESS_SWITCH.objects.filter(
                                                port_type__in = PORT_TYPE.objects.filter(
                                                                    connection_type__in = (0,1)
                                                                    ),
                                                access_switch__in = ACCESS_SWITCH.objects.filter(
                                                                    access_node__in = ACCESS_NODE.objects.filter(
                                                                                        thread = self.access_switch.access_node.thread
                                                                                        )
                                                                    )
                                                )
                    #print(uplink_ports_in_thread)
                    for port in uplink_ports_in_thread:
                        port.save_uplink()

    # процедура специально для обновления аплинков и распред портов
    def save_uplink(self):
        if self.port_type.id in (0, 1):
            print(self)
            # то меняем значение u_vlan на 1, а t_vlans на список вланов в нитке, к которой относится коммутатора
            self.description = self.port_type.default_description
            self.default_u_vlan()
            # а значение t_vlans на список всех используемых в нитке вланов
            vlans_in_thread = self.access_switch.access_node.thread.used_vlans()
            vlans = net_lib.interval_to_arr(GUTS_CONSTANTS['PERMANENT_VLANS'])
            for vlan in vlans_in_thread.keys():
                if vlan not in vlans:
                    vlans.append(vlan)
            vlans.append(int(GUTS_CONSTANTS['MGMT_VLAN']))
            print('t_VLANS >>> ', net_lib.arr_to_interval(vlans))
            self.t_vlans = net_lib.arr_to_interval(vlans)
        self.save()
        
        
    def default_u_vlan(self):
        type_id = self.port_type.id
        #Если порт для пппое то вычисляем для него уникальный pppoe-влан
        if type_id == 3:
            current_count_access_switches_in_thread = ACCESS_SWITCH.objects.filter(
                access_node__in=ACCESS_NODE.objects.filter(
                    thread = self.access_switch.access_node.thread
                )
            ).count()
            pppoe_vlan = 50 * (19 + current_count_access_switches_in_thread) + self.num_in_switch
            self.u_vlan = pppoe_vlan
        # для портов расширения и аплинков необходимо добавить default vlan
        if type_id in (0, 1):
            self.u_vlan = 1
        
def dlink_cfg(access_switch):
    # определяем шаблон конфигурации по модели коммутатора
    template_file = access_switch.sw_model.cfg_template
    dst_file = '%s_%s.cfg' % (access_switch.pk, timezone.now().strftime('%Y%m%d_%H%M'))
    # Если определен шаблон конфига пытаемся его открыть
    if template_file != '':
        # Пытаемся открыть файл шаблона конфигурации
        try:
            template = open(template_file.path).read()
        except IOError as err_str:
            print('ERROR!!! Неудалось прочитать файл шаблона!!!')
            print('< ' + str(err_str) + ' >')
            return
        # Пытаемся создать файл конфигурации для данного коммутатора
        try:
            tmp_cfg_file_path = '/tmp/guts_cfg.tmp'
            cfg_file = open(tmp_cfg_file_path,"w").close()
            cfg_file = open(tmp_cfg_file_path,"r+")
        except IOError as err_str:
            print('ERROR!!! Неудалось создать файл для записи конфига!!!')
            print('< ' + str(err_str) + ' >')
            return
        ##############################################################################################
        #<THREAD_NUM>           номер нитки (111-1)
        THREAD_NUM = '%s-%s.%s.%s-%s' % (
                    access_switch.access_node.thread.campus.prefix,
                    access_switch.access_node.thread.campus.ms.mgs.mgs_num,
                    access_switch.access_node.thread.campus.ms.num_in_mgs,
                    access_switch.access_node.thread.campus.num_in_ms,
                    access_switch.access_node.thread.num_in_campus)
        template = re.sub('<THREAD_NUM>', THREAD_NUM, template)
        
        ##############################################################################################
        #<ADDRESS>              адрес_латиницей
        ADDRESS = net_lib.translit(access_switch.access_node.address)
        template = re.sub('<ADDRESS>', ADDRESS, template)
        
        ##############################################################################################
        #<SNMP_CONTACT>         
        SNMP_CONTACT = GUTS_CONSTANTS['SNMP_CONTACT']
        template = re.sub('<SNMP_CONTACT>', SNMP_CONTACT, template)
        
        ##############################################################################################
        #<CLIENTS_PORTS>        порты с клиентскими подключениями (все кроме бэкбонов, и сигнальных)
        clients_ports_list = list(access_switch.clients_ports().values_list('num_in_switch', flat = True))
        CLIENTS_PORTS = net_lib.arr_to_interval(clients_ports_list)
        template = re.sub('<CLIENTS_PORTS>', CLIENTS_PORTS, template)
        
        ##############################################################################################
        #<PPPOE_PORTS>          порты pppoe-клиентов
        pppoe_ports_list = list(access_switch.pppoe_ports().values_list('num_in_switch', flat = True))
        PPPOE_PORTS = net_lib.arr_to_interval(pppoe_ports_list)
        template = re.sub('<PPPOE_PORTS>', PPPOE_PORTS, template)
        
        ##############################################################################################
        #<IP_PORTS>             порты на которых разрешен ip-трафик (не pppoe)
        ip_ports_list = list(access_switch.ip_ports().values_list('num_in_switch', flat = True))
        IP_PORTS = net_lib.arr_to_interval(ip_ports_list)
        template = re.sub('<IP_PORTS>', IP_PORTS, template)
        
        ##############################################################################################
        #<BACKBON_PORTS>        порты аплинки+порты расширения
        backbon_ports_list = list(access_switch.backbon_ports().values_list('num_in_switch', flat = True))
        BACKBON_PORTS = net_lib.arr_to_interval(backbon_ports_list)
        template = re.sub('<BACKBON_PORTS>', BACKBON_PORTS, template)
        
        ##############################################################################################
        #<NOT_BACKBON_PORTS>    порты кроме аплинков и портов расширения
        not_backbon_ports_list = list(access_switch.not_backbon_ports().values_list('num_in_switch', flat = True))
        NOT_BACKBON_PORTS = net_lib.arr_to_interval(not_backbon_ports_list)
        template = re.sub('<NOT_BACKBON_PORTS>', NOT_BACKBON_PORTS, template)
        
        ##############################################################################################
        #<MGMT_VLAN>              номер влана управления коммутатора
        MGMT_VLAN = GUTS_CONSTANTS['MGMT_VLAN']
        template = re.sub('<MGMT_VLAN>', MGMT_VLAN, template)
        
        ##############################################################################################
        #<MGMT_IP>              ip-адрес коммутатора
        MGMT_IP = access_switch.ip
        template = re.sub('<MGMT_IP>', MGMT_IP, template)
        
        ##############################################################################################
        #<MGMT_LONG_MASK>       маска подсети управления
        if not access_switch.network:
            access_switch.save()
        MGMT_LONG_MASK = str(ipaddress.ip_network(access_switch.network).netmask)
        template = re.sub('<MGMT_LONG_MASK>', MGMT_LONG_MASK, template)
        
        ##############################################################################################
        #<GW>                   ip-адрес шлюза поумолчанию
        GW = access_switch.network.gw
        template = re.sub('<GW>', GW, template)
        
        ##############################################################################################
        #<ID>                   id коммутатора
        ID = access_switch.pk
        template = re.sub('<ID>', str(ID), template)
        
        ##############################################################################################
        #<ADMIN_PROXY_IP>       
        ADMIN_PROXY_IP = GUTS_CONSTANTS['ADMIN_PROXY_IP']
        template = re.sub('<ADMIN_PROXY_IP>', ADMIN_PROXY_IP, template)
        
        ##############################################################################################
        #<EQM_IP>
        EQM_IP = GUTS_CONSTANTS['EQM_IP']
        template = re.sub('<EQM_IP>', EQM_IP, template)
        
        ##############################################################################################
        #<NS4_IP>
        NS4_IP = GUTS_CONSTANTS['NS4_IP']
        template = re.sub('<NS4_IP>', NS4_IP, template)
        
        ##############################################################################################
        #<NS2_IP>
        NS2_IP = GUTS_CONSTANTS['NS2_IP']
        template = re.sub('<NS2_IP>', NS2_IP, template)
        
        ##############################################################################################
        #<RADIUS1_IP>
        RADIUS1_IP = GUTS_CONSTANTS['RADIUS1_IP']
        template = re.sub('<RADIUS1_IP>', RADIUS1_IP, template)
        
        ##############################################################################################
        #<RADIUS2_IP>
        RADIUS2_IP = GUTS_CONSTANTS['RADIUS2_IP']
        template = re.sub('<RADIUS2_IP>', RADIUS2_IP, template)
        
        ##############################################################################################
        #<radius_port>
        radius_port = GUTS_CONSTANTS['radius_port']
        template = re.sub('<radius_port>', radius_port, template)
        
        ##############################################################################################
        #<radius_key>
        radius_key = GUTS_CONSTANTS['radius_key']
        template = re.sub('<radius_key>', radius_key, template)
        
        ##############################################################################################
        # <acct_port>
        acct_port = GUTS_CONSTANTS['acct_port']
        template = re.sub('<acct_port>', acct_port, template)
        
        ##############################################################################################
        #<TIME_ZONE>
        TIME_ZONE = GUTS_CONSTANTS['TIME_ZONE']
        template = re.sub('<TIME_ZONE>', TIME_ZONE, template)
        
        ##############################################################################################
        #<STP_PRIORITY>
        if access_switch.stp_root:
            STP_PRIORITY = '28672'
        else:
            STP_PRIORITY = '32768'
        template = re.sub('<STP_PRIORITY>', str(STP_PRIORITY), template)
        
        ##############################################################################################
        #<CONF_VLAN>                Настройи вланов
        CONF_VLAN = ''
        used_vlans = access_switch.used_vlans()
        for vlan in sorted(used_vlans.keys()):
            if vlan not in [0,1]:
                CONF_VLAN += 'create vlan %s tag %s\n' % (vlan, vlan)
        for port in access_switch.port_of_access_switch_set.all():
            if port.u_vlan not in [0,1]:
                CONF_VLAN += 'conf vlan %s add untagged %s advertisement disable\n' % (vlan, port.num_in_switch)
            for vlan in net_lib.interval_to_arr(port.t_vlans):
                if vlan not in [0,1]:
                    CONF_VLAN += 'conf vlan %s add tagged %s advertisement disable\n' % (vlan, port.num_in_switch)
            
        template = re.sub('<CONF_VLAN>', str(CONF_VLAN), template)
        
        ##############################################################################################
        #<CONF_TRAF_SEGMENTATION>   Настройки traffic segmentation
        #config traffic_segmentation <downlink_ports> forward_list <uplink_ports>
        #config traffic_segmentation <uplink_ports> forward_list <downlink_ports>
        #config traffic_segmentation <gag_ports> forward_list null
        uplink_ports_list = list(access_switch.uplink_ports().values_list('num_in_switch', flat = True))
        downlink_ports_list = list(access_switch.downlink_ports().values_list('num_in_switch', flat = True))
        gag_ports_list = list(access_switch.gag_ports().values_list('num_in_switch', flat = True))
        UPLINK_PORTS = net_lib.arr_to_interval(uplink_ports_list)
        DOWNLINK_PORTS = net_lib.arr_to_interval(downlink_ports_list)
        GAG_PORTS = net_lib.arr_to_interval(gag_ports_list)
        CONF_TRAF_SEGMENTATION = "config traffic_segmentation %s forward_list %s\n" % (DOWNLINK_PORTS, UPLINK_PORTS)
        CONF_TRAF_SEGMENTATION += "config traffic_segmentation %s forward_list %s\n" % (GAG_PORTS, DOWNLINK_PORTS)
        if GAG_PORTS != '':
            CONF_TRAF_SEGMENTATION += "config traffic_segmentation %s forward_list null\n" % GAG_PORTS
        
        template = re.sub('<CONF_TRAF_SEGMENTATION>', CONF_TRAF_SEGMENTATION, template)
        
        ##############################################################################################
        #<PORTS_DESCRIPTION>
        PORTS_DESCRIPTION = ''
        for port in access_switch.port_of_access_switch_set.all():
            description = net_lib.translit(port.description)
            PORTS_DESCRIPTION += 'configure ports %s description "%s"\n' % (port.num_in_switch, description)
        template = re.sub('<PORTS_DESCRIPTION>', PORTS_DESCRIPTION, template)
            
        ##############################################################################################
        #<SNMP_RW_COMMUNITY>
        SNMP_RW_COMMUNITY = GUTS_CONSTANTS['SNMP_RW_COMMUNITY']
        template = re.sub('<SNMP_RW_COMMUNITY>', SNMP_RW_COMMUNITY, template)
        
        template = re.sub('<TEST>', '', template)
        try:
            cfg_file.write(template)
            access_switch.cfg_file.save(dst_file,File(cfg_file),save=False)
            # Закрываем и удаляем временный файл
            cfg_file.close()
        except IOError as err_str:
            print('ERROR!!! Неудалось записать файл для записи конфига!!!')
            print('< ' + str(err_str) + ' >')
            return
        os.remove(tmp_cfg_file_path)
        access_switch.save()
    
