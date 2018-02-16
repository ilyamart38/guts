from django.db import models

# Класс описывающий объект МГС
class MGS(models.Model):
	# Название (МГС-1, МГС-2 и пр.)
	Title = models.CharField(max_length = 20)
	# Адрес МГС
	Address = models.CharField(max_length = 100)

	# Представление МГС
	def __str__(self):
		return self.Title

# Класс описывающий объект кампуса (ППК/МКУ)
class CAMPUS(models.Model):
	# Название (ППК-1.1.1, МКУ-8.2.1 и пр.)
	Title = models.CharField(max_length = 20)
	# Принадлежность к МГС
	mgs = models.ForeignKey(MGS, on_delete=models.CASCADE)

	# Представление кампуса
	def __str__(self):
		return self.Title

# Класс описывающий нитку, соответствующую одному l2-сегменту в пределах МГС
class THREAD(models.Model):
	# Название нитки (1.1.1-1, 8.2.1-1)
	Title = models.CharField(max_length = 20)
	OutVlan = models.IntegerField(default = 0)
	campus = models.ForeignKey(CAMPUS, on_delete = models.CASCADE)
	AggInterface = models.CharField(max_length = 100, default = "")
	Kommutation = models.CharField(max_length = 100, default = "")
	
	# Представление нитки
	def __str__(self):
		return self.Title

# Класс описывающий подсеть устройств
class SUBNET(models.Model):
	# адрес сети
	network = models.CharField(max_length = 15)
	# маска сети
	mask = models.IntegerField(default=28)
	# минимальный адрес
	HostMin = models.CharField(max_length = 15)
	# максимальный адрес
	HosMax = models.CharField(max_length = 15)
	#Нитка в которой используется данная подсеть
	thread = models.ForeignKey(THREAD, on_delete = models.CASCADE)

	# Представление подсети
	def __str__(self):
		return "%s/%s" % (self.network, self.mask)

