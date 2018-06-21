from django.db import models
from clients.models import CLIENTS

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
import SubnetTree
import ipaddress
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

# Класс описывающий vlan
#class VLAN(models.Model):
#    class Meta:
#        verbose_name = "vlan"
#
#    vid = models.IntegerField(primary_key=True, verbose_name="vlan")
#    
#    def __str__(self):
#        return "%s" % self.vid

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
    
    # Представление МГС
    def __str__(self):
        return "МГС-%s" % self.mgs_num

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
    
    # Представление кампуса
    def __str__(self):
        return "%s-%s.%s.%s" % (self.get_prefix_display(), self.ms.mgs.mgs_num, self.ms.num_in_mgs, self.num_in_ms)
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('campus', args=[str(self.id)])
    
    def access_node_count(self):
        node_count = 0
        for thread in self.thread_set.all():
            node_count += thread.access_node_set.count()
        return node_count

    def access_sw_count(self):
        sw_count = 0
        for thread in self.thread_set.all():
            for node in thread.access_node_set.all():
                sw_count += node.access_switch_set.count()
        return sw_count

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

    # Представление нитки
    def __str__(self):
        return "%s-%s" % (self.campus, self.num_in_campus)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('campus', args=[str(self.campus.id)])
    
    # Процедура определения списка вланов используемого в нитке
    def used_vlans(self):
        used_vlans = {}
        # список узлов в нитке
        nodes_in_thread = ACCESS_NODE.objects.filter(thread = self)
        # список коммутаторов в нитке
        switches_in_thread = ACCESS_SWITCH.objects.filter(access_node__in = nodes_in_thread)
        # список портов на всех коммутаторах в нитке:
        ports_in_thread = PORT_OF_ACCESS_SWITCH.objects.filter(access_switch__in = switches_in_thread)
        # перебераем каждый порт
        for port in ports_in_thread:
            # изучаем вланы на всех портах кроме аплинков и распред.портов!
            if port.port_type.id not in (0, 1):
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
        #print(used_vlans)
        #print(net_lib.arr_to_interval(used_vlans.keys()))
        return used_vlans

# Класс описывающий подсеть устройств
class SUBNET(models.Model):
    class Meta:
        verbose_name = "Подсеть"
        verbose_name_plural = "Подсети"
    
    # адрес сети
    network = models.CharField(max_length = 18)
    #Нитка в которой используется данная подсеть
    thread = models.ForeignKey(THREAD, on_delete=models.CASCADE, blank=True, null=True, default=None)

    # Представление подсети
    def __str__(self):
        return "%s" % (self.network)
    
    def clean(self):
        validator_net_addr(self.network)
        validator_subnet(self)
    
    def ip_address(self):
        list_ip=[]
        ip_net = ipaddress.ip_network(self.network)
        for ip in ip_net:
            if ip not in (ip_net.network_address, ip_net.broadcast_address-1, ip_net.broadcast_address):
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
        return reverse('subnet', args=[str(self.id)])
    
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
    fw_version = models.CharField(max_length = 100, blank = True, verbose_name = 'Рекомендованная версия ПО')
    hw_version = models.CharField(max_length = 100, blank = True, verbose_name = 'HW версия')
    ports_count = models.IntegerField(default = 0, verbose_name = 'Количество портов')
    ports_names = models.CharField(max_length = 500, blank = True, verbose_name = 'Названия портов в конфиге')
    ports_types = models.CharField(max_length = 200, blank = True, verbose_name = 'Типы портов по умолчанию', help_text = create_help_text_for_type_ports())
    cfg_template = models.CharField(max_length = 100, blank = True)

    # Представление модели коммутатора
    def __str__(self):
        return "%s %s" % (self.vendor, self.title)
    
    def clean(self):
        if len(self.ports_types.split(',')) != self.ports_count:
            raise ValidationError('Настройки типов портов не соответствуют введенному количеству портов! (%s != %s)' % (len(self.ports_types.split(',')), self.ports_count))
        if len(self.ports_names.split(',')) != self.ports_count:
            raise ValidationError('Настройки названий портов не соответствуют введенному количеству портов! (%s != %s)' % (len(self.ports_names.split(',')), self.ports_count))
        for port_type in self.ports_types.split(','):
            print(port_type, PORT_TYPE.objects.filter(id=port_type), PORT_TYPE.objects.filter(id=port_type).count())
            if PORT_TYPE.objects.filter(id=port_type).count() == 0:
                raise ValidationError('Введен неопределенный тип порта! (%s)' % port_type)

# Класс описывающий узел уровня доступа
class ACCESS_NODE(models.Model):
    class Meta:
        verbose_name = "Узел доступа"
        verbose_name_plural = "Узлы доступа"

    address = models.CharField(max_length = 100, unique=True)
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

    # Представление коммутатора доступа
    def __str__(self):
        address = self.access_node.address
        ip = self.ip
        return "%s (%s)" % (address, ip)
    
    def save(self, *args, **kwargs):
        # если происходит обновление данных существующего коммутатора
        if ACCESS_SWITCH.objects.filter(id = self.id):
            # Если задана модель коммутатора
            if self.sw_model:
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
#                            port_name = self.sw_model.ports_names.split(',')[port_num-1]
#                            port_type = PORT_TYPE.objects.get(id=self.sw_model.ports_types.split(',')[port_num-1]),
#                            description = PORT_TYPE.objects.get(id=self.sw_model.ports_types.split(',')[port_num-1]).default_description
                        )
                    # Если порт старый и был/стал аплинком или портом расширения, то меняем настройки в соответствии с новой моделью
                    elif ports.get(num_in_switch=port_num).port_type.id in (0, 1) or PORT_TYPE.objects.get(id=self.sw_model.ports_types.split(',')[port_num-1]).id in (0, 1):
                        # Меняем настройки порта port_num
                        print ('Меняем настройки порта', port_num, PORT_TYPE.objects.get(id=self.sw_model.ports_types.split(',')[port_num-1]))
                        edit_port = ports.get(num_in_switch=port_num)
                        edit_port.port_type =  PORT_TYPE.objects.get(id=self.sw_model.ports_types.split(',')[port_num-1])
                        edit_port.description = PORT_TYPE.objects.get(id=self.sw_model.ports_types.split(',')[port_num-1]).default_description
                        edit_port.default_u_vlan()
                        edit_port.port_name = self.sw_model.ports_names.split(',')[port_num-1]
                        edit_port.save()
                    else:
                        edit_port = ports.get(num_in_switch=port_num)
                        print('БЕЗ ИЗМЕНЕНИЙ!', ports.get(num_in_switch=port_num), 'type =',ports.get(num_in_switch=port_num).port_type.id, ') / ', PORT_TYPE.objects.get(id=self.sw_model.ports_types.split(',')[port_num-1]))
                        edit_port.port_name = self.sw_model.ports_names.split(',')[port_num-1]
                        print(self.sw_model.ports_names.split(',')[port_num-1])
                        edit_port.save()
                # в случае если портов стало меньше, удаляем старые порты
                for port in ports:
                    if port.num_in_switch not in range(1, self.sw_model.ports_count+1):
                        #print('Удаление порта', port.num_in_switch)
                        port.delete()
            super(ACCESS_SWITCH, self).save(*args, **kwargs)
        # если происходит добавление нового коммутатора
        else:
            super(ACCESS_SWITCH, self).save(*args, **kwargs)
            if self.sw_model:
                for port_num in range(1, self.sw_model.ports_count+1):
                    self.port_of_access_switch_set.create(
                        num_in_switch = port_num,
                        port_name = self.sw_model.ports_names.split(',')[port_num-1]
                        )
                    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('access_switch', args=[str(self.id)])   
    def port_type(self, port):
        if port in range(1, self.ports_count+1):
            return self.ports_types.split(',')[port-1]
        else:
            return None
    def ports(self):
        return range(1,self.sw_model.ports_count+1)

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
    #non_pppoe = models.BooleanField(default=False)
    #is_signal = models.BooleanField(default=False)
    #is_upstream = models.BooleanField(default=False)
    #is_bad = models.BooleanField(default=False, verbose_name = 'Нерабочий')
    
    u_vlan = models.IntegerField(default = 0, verbose_name = 'Untag-vlan/PVID')
    t_vlans = models.CharField(max_length = 100, blank =True)
    def __str__(self):
        return '%s (%s)' % (self.access_switch, self.num_in_switch)
        
    def clean(self):
        if self.u_vlan < 0:
            raise ValidationError('Значение Untag-vlan не может быть отрицательным!!!')
        elif self.u_vlan > 4094:
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
                # то меняем значение u_vlan на 1, а t_vlans на список вланов в нитке, к которой относится коммутатора
                self.description = self.port_type.default_description
                self.default_u_vlan()
                # а значение t_vlans на список всех используемых в нитке вланов
                vlans_in_thread = self.access_switch.access_node.thread.used_vlans()
                self.t_vlans = net_lib.arr_to_interval(vlans_in_thread.keys())

        # если происходит изменение настроек сущеcтвующего порта то следуем определенным правилам
        else:
            # порт до изменений
            current_port = PORT_OF_ACCESS_SWITCH.objects.get(id=self.id)
            # 1. проверяем изменился ли тип порта
            if self.port_type != current_port.port_type:
                # Если новое значение соответствует магистральному или распределительному порту
                if self.port_type.id in (0, 1):
                    # то меняем значение u_vlan на 1, а t_vlans на список вланов в нитке, к которой относится коммутатора
                    self.description = self.port_type.default_description
                    self.default_u_vlan()
                    # а значение t_vlans на список всех используемых в нитке вланов
                    vlans_in_thread = self.access_switch.access_node.thread.used_vlans()
                    self.t_vlans = net_lib.arr_to_interval(vlans_in_thread.keys())
                # Если новое значение соответствует клиентскому pppoe-порту
                elif self.port_type.id == 3:
                    # В любом случае убираем все тегированные вланы с порта
                    self.t_vlans = ''
                    # Если не изменили описание порта, то выставляем значение поумолчению
                    if self.description == current_port.description:
                        self.description = self.port_type.default_description
                    # Если не изменился клиентский влан, то выставляем влан поумолчанию
                    if self.u_vlan == current_port.u_vlan:
                        self.default_u_vlan()
                # Если новое значение соответствует прочему клиентскому (не pppoe) порту
                elif self.port_type.id == 4:
                    # Если не изменили описание порта, то выставляем значение поумолчению
                    if self.description == current_port.description:
                        self.description = self.port_type.default_description
                    # Значение вланов оставляем без изменений
                # Если новое значение соответствует порту какого-либо сигнализатора, или неисправного порта
                elif self.port_type.id in (5,99):
                    # Если не изменили описание порта, то выставляем значение поумолчению
                    if self.description == current_port.description:
                        self.description = self.port_type.default_description
                    # Убираем все вланы с портов
                    self.u_vlan = 0
                    self.t_vlans = ''
            pass
        super(PORT_OF_ACCESS_SWITCH, self).save(*args, **kwargs)
    
    # процедура специально для обновления аплинков и распред портов
    def save_uplink(self):
        if self.port_type.id in (0, 1):
            # то меняем значение u_vlan на 1, а t_vlans на список вланов в нитке, к которой относится коммутатора
            self.description = self.port_type.default_description
            self.default_u_vlan()
            # а значение t_vlans на список всех используемых в нитке вланов
            vlans_in_thread = self.access_switch.access_node.thread.used_vlans()
            self.t_vlans = net_lib.arr_to_interval(vlans_in_thread.keys())
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
        
