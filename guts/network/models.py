from django.db import models
from clients.models import CLIENTS

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

	# Название (МГС-1, МГС-2 и пр.)
	title = models.CharField(max_length = 20)
	# Адрес МГС
	address = models.CharField(max_length = 100)
	lag = models.ForeignKey(LAG, on_delete = models.SET_NULL, blank=True, null=True)
	
	# Представление МГС
	def __str__(self):
		return self.title

# (4) Класс описывающий объект кампуса (ППК/МКУ)
class CAMPUS(models.Model):
	class Meta:
		verbose_name = "Кампус"
		verbose_name_plural = "Кампусы"
		ordering = ['title']

	# Название (ППК-1.1.1, МКУ-8.2.1 и пр.)
	title = models.CharField(max_length = 20)
	# Принадлежность к МГС
	mgs = models.ForeignKey(MGS, on_delete=models.CASCADE)

	# Представление кампуса
	def __str__(self):
		return self.title

# (5) Класс описывающий нитку, соответствующую одному l2-сегменту в пределах МГС
class THREAD(models.Model):
	class Meta:
		verbose_name = "Нитка"
		verbose_name_plural = "Нитки"
		unique_together = ('campus', 'num_in_campus',)


	# Название нитки (1.1.1-1, 8.2.1-1)
	title = models.CharField(max_length = 20)
	campus = models.ForeignKey(CAMPUS, on_delete = models.CASCADE)
	num_in_campus = models.IntegerField(default = 1)
	outvlan = models.ForeignKey(VLAN, on_delete = models.SET_NULL, blank=True, null=True, related_name = 'outvlan')
	mapvlan = models.ForeignKey(VLAN, on_delete = models.SET_NULL, blank=True, null=True, related_name = 'mapvlan')

	# Представление нитки
	def __str__(self):
		campus = self.campus.title
		return "%s(%s)" % (self.campus, self.num_in_campus)

# (6) Класс описывающий подсеть устройств
class SUBNET(models.Model):
	class Meta:
		verbose_name = "Подсеть"
		verbose_name_plural = "Подсети"

	# адрес сети
	network = models.GenericIPAddressField(protocol = 'IPv4')
	# маска сети
	mask = models.IntegerField(default=28)
	# минимальный адрес
	hostmin = models.GenericIPAddressField(protocol = 'IPv4')
	# максимальный адрес
	hosmax = models.GenericIPAddressField(protocol = 'IPv4')
	#Нитка в которой используется данная подсеть
	thread = models.ForeignKey(THREAD, on_delete = models.CASCADE)

	# Представление подсети
	def __str__(self):
		return "%s/%s" % (self.network, self.mask)


## (7) Класс описывающий ip-адрес
#class IP_ADDRESS(models.Model):
#	ip_addr = models.CharField(max_length = 15)
#	net = models.ForeignKey(SUBNET, on_delete = models.CASCADE)
#	atomic = False
#	
#	# Представление ip-адреса
#	def __str__(self):
#		return self.ip_addr
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
		th = self.thread.title
		campus = self.thread.campus.title
		return "%s (%s-%s)" % (self.address, campus, th)

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

