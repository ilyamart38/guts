from django.db import models
from clients.models import CLIENTS

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
import SubnetTree
import ipaddress

#Валидатор проверки корректности введенного адреса подсети
def check_subnet_address(subnet):
    #1. проверяем, является ли переданное значение адресом подсети
    try:
        subnet = ipaddress.ip_network(subnet)
        #Разрешаем использовать сети не короче /30
        if subnet.prefixlen > 30:
            raise ValidationError('Для сети не разрешено использовать префикс больше 30!')
    except ValueError:
        raise ValidationError('Введенные данные не могут являться адресом подсети!')


# Валидатор корректности записи подсети IPv4 (0-255).(0-255).(0-255).(0-255)/(0-32)
ip_net_regex =  '^(([1-9]?[0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])\.){3}([0-1]?[0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5]\.)/((3[0-2])|([1-2]?[0-9]))$'
net_validator = RegexValidator(regex=ip_net_regex, message="Введенный адрес сети не соответствует стандарту! Введите значение в формате xxx.xxx.xxx.xxx/nn")


# Класс описывающий vlan
class VLAN(models.Model):
    class Meta:
        verbose_name = "vlan"

    vid = models.IntegerField(primary_key=True, verbose_name="vlan")
    
    def __str__(self):
        return "%s" % self.vid

# (1) Класс описывающий lag
class LAG(models.Model):
    title = models.IntegerField(default = 0)
    
    def __str__(self):
        return "lag-%s" % self.title

# (2) Класс описывающий sap
class SAP(models.Model):
    title = models.CharField(max_length=100)
    lag = models.ForeignKey(LAG, on_delete = models.SET_NULL, blank=True, null=True)
    s_vlan = models.ForeignKey(VLAN, on_delete = models.SET_NULL, blank=True, null=True, related_name = 'svlan')
    c_vlan = models.ForeignKey(VLAN, on_delete = models.SET_NULL, blank=True, null=True, related_name = 'cvlan')
    
    def __str__(self):
        return "%s:%s.%s (%s)" % (self.lag, self.s_vlan, self.c_vlan, self.title)

# (3) Класс описывающий объект МГС
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

# Модель описывающая объект магистрали
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

# (4) Класс описывающий объект кампуса (ППК/МКУ)
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

# (5) Класс описывающий нитку, соответствующую одному l2-сегменту в пределах МГС
class THREAD(models.Model):
    class Meta:
        verbose_name = "Нитка"
        verbose_name_plural = "Нитки"
        unique_together = ('campus', 'num_in_campus',)

    # Название нитки (1.1.1-1, 8.2.1-1)
    #title = models.CharField(max_length = 20)
    campus = models.ForeignKey(CAMPUS, on_delete = models.CASCADE)
    num_in_campus = models.IntegerField(default = 1)
    outvlan = models.ForeignKey(VLAN, on_delete = models.SET_NULL, blank=True, null=True, related_name = 'outvlan')
    mapvlan = models.ForeignKey(VLAN, on_delete = models.SET_NULL, blank=True, null=True, related_name = 'mapvlan')

    # Представление нитки
    def __str__(self):
        return "%s-%s" % (self.campus, self.num_in_campus)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('campus', args=[str(self.campus.id)])

# (6) Класс описывающий подсеть устройств
class SUBNET(models.Model):
    class Meta:
        verbose_name = "Подсеть"
        verbose_name_plural = "Подсети"
    
    # адрес сети
    network = models.CharField(max_length = 18, validators=[check_subnet_address])
    #Нитка в которой используется данная подсеть
    thread = models.ForeignKey(THREAD, on_delete = models.SET_NULL, blank=True, null=True)

    # Представление подсети
    def __str__(self):
        return "%s" % (self.network)
    
    def clean(self):
        # Запоминаем заданную сеть
        curr_net = SubnetTree.SubnetTree()
        curr_net[self.network] = 'curr_net'
        
        # Далее сети использующиеся на сети
        # ------------------------!!! Необходимо вынести в отдельный класс !!!---------------------------
        guts_net = SubnetTree.SubnetTree()
        guts_net['10.225.16.0/20'] = 'МГС-1'
        guts_net['10.225.32.0/20'] = 'МГС-2'
        guts_net['10.225.48.0/20'] = 'МГС-3'
        guts_net['10.225.64.0/20'] = 'МГС-4'
        guts_net['10.225.80.0/20'] = 'МГС-5'
        guts_net['10.225.96.0/20'] = 'МГС-6'
        guts_net['10.225.112.0/20'] = 'МГС-7'
        guts_net['10.225.128.0/20'] = 'МГС-8'
        guts_net['10.225.144.0/20'] = 'МГС-9'
        guts_net['10.225.160.0/20'] = 'МГС-10'
        guts_net['10.225.176.0/20'] = 'МГС-11'
        guts_net['10.225.192.0/20'] = 'МГС-12'
        guts_net['10.225.208.0/20'] = 'МГС-13'
        guts_net['10.225.224.0/20'] = 'МГС-14'
        guts_net['10.225.240.0/20'] = 'МГС-15'
        
        # проверяем можноли использовать введенные данные на нашей сети
        if self.network not in guts_net:
            raise ValidationError("Адрес не принадлежит адресам разрешенным в ГУТС города!")
        
        # проверяем не используются ли введенные данные в какой-либо нитке
        # Перебираем в каждой нитке
        for thread in THREAD.objects.all():
            thread_net = SubnetTree.SubnetTree()
            # каждую подсеть
            for subnet in thread.subnet_set.all():
                # исключая случай когда нажали сохранить без внесения изменений
                if subnet != self:
                    thread_net[subnet.network] = 'thread_net'
                    # если введенные данные уже где-то используются то говорим "Ай-ай-ай!!!"
                    if self.network in thread_net:
                        raise ValidationError("Указанный адрес сети не может использоваться т.к. входит в %s (%s)!" % (thread, subnet.network))
                    # также говорим "Ай-ай-ай!!!" если подсеть в какой-либо нитке входит в веденную сеть
                    if subnet.network in curr_net:
                        raise ValidationError("Указанный адрес сети не может использоваться т.к. в него входит уже занятая подсеть %s (%s)!" % (thread, subnet.network))

class VENDORS(models.Model):
    class Meta:
        verbose_name = "Вендор"
        verbose_name_plural = "Вендоры"
    
    title = models.CharField(max_length = 100)
    
    def __str__(self):
        return self.title

# (8) Класс описывающий модель коммутатора
class SW_MODEL(models.Model):
    class Meta:
        verbose_name = "Модель коммутаторов"
        verbose_name_plural = "Модели коммутаторов"


    vendor = models.ForeignKey(VENDORS, on_delete = models.SET_NULL, blank=True, null=True)
    title = models.CharField(max_length = 100)
    fw_version = models.CharField(max_length = 100, blank = True)
    hw_version = models.CharField(max_length = 100, blank = True)
    ports_count = models.IntegerField(default = 0)
    ports_types = models.CharField(max_length = 100, blank = True)
    cfg_template = models.CharField(max_length = 100, blank = True)

    # Представление модели коммутатора
    def __str__(self):
        return "%s %s" % (self.vendor, self.title)

# (9) Класс описывающий узел уровня доступа
class ACCESS_NODE(models.Model):
    class Meta:
        verbose_name = "Узел доступа"
        verbose_name_plural = "Узлы доступа"

    address = models.CharField(max_length = 100)
    thread = models.ForeignKey(THREAD, on_delete = models.CASCADE)

    # Представление узла
    def __str__(self):
        return "%s (%s)" % (self.address, self.thread)

# (10) Класс описывающий коммутатор уровня доступа
class ACCESS_SWITCH(models.Model):
    class Meta:
        verbose_name = "Коммутатор доступа"
        verbose_name_plural = "Коммутаторы доступа"

    access_node = models.ForeignKey(ACCESS_NODE, on_delete = models.CASCADE)
    sw_model = models.ForeignKey(SW_MODEL, on_delete = models.SET_NULL, blank=True, null=True)
    ip = models.GenericIPAddressField(protocol = 'IPv4', unique=True)
    subnet = models.ForeignKey(SUBNET, on_delete = models.SET_NULL, blank=True, null=True)
    ports_count = models.IntegerField(default = 0)
    ports_types = models.CharField(max_length = 100, blank =True)
    u_vlans = models.CharField(max_length = 500, blank = True)
    t_vlans = models.CharField(max_length = 500, blank = True)

    # Представление коммутатора доступа
    def __str__(self):
        address = self.access_node.address
        ip = self.ip
        return "%s (%s)" % (address, ip)

