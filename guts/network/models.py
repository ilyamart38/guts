from django.db import models

# Класс описывающий объект МГС
class MGS(models.Model):
	# Название (МГС-1, МГС-2 и пр.)
	Title = models.CharField(max_length = 20)
	# Адрес МГС
	Address = models.CharField(max_length = 100)

# Класс описывающий объект кампуса (ППК/МКУ)
class CAMPUS(models.Model):
	# Название (ППК-1.1.1, МКУ-8.2.1 и пр.)
	Title = models.CharField(max_length = 20)
	# Принадлежность к МГС
	mgs = models.ForeignKey(MGS, on_delete=models.CASCADE)

## Класс описывающий нитку, соответствующую одному l2-сегменту в пределах МГС
#class THREAD(models.Model):
