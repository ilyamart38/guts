# проверка соответствия номера МС концепции
# Концептуально МС не может превышать 8
def check_concept_ms(ms_num):
	if ms_num > 8:
		return False
	else:
		return True

# проверка соответствия номера кампуса концепции
# Концептуально номер кампуса в магистрале не может превышать 9
def check_concept_campus(campus_num):
	if campus_num > 9:
		return False
	else:
		return True

# проверка соответствия номера нитки в кампусе концепции
# Концептуально номер нитки в кампусе не может превышать 4
def check_concept_tread(thread_num):
	if thread_num > 4:
		return False
	else:
		return True

# вычисление map-vlan
def calculation_mapvlan(ms_num, campus_num, thread_num):
	if check_concept_ms(ms_num) and check_concept_campus(campus_num) and check_concept_tread(thread_num):
		# Если кампус 9-й в магистрале (1.3.9) то для него вычисляются вланы как для соответствующего (номеру МС) компуса в 7-й магистрале (1.7.3)
		if (campus_num == 9):
			campus_num = ms_num
			ms_num = 7
		map_vlan = 470+(ms_num-1)*32+(campus_num-1)*4+(thread_num-1)
		return map_vlan
	else:
		return False

# вычисление out_vlan
def calculation_outvlan(mgs_num, ms_num, campus_num, thread_num):
	if check_concept_ms(ms_num) and check_concept_campus(campus_num) and check_concept_tread(thread_num):
		# т.к. номер МГС концептуально не может быть больше 15, то выделяем соответствующий номер МГС
		mgs_num %= 15
		
		# Если кампус 9-й в магистрале (1.3.9) то для него вычисляются вланы как для соответствующего (номеру МС) компуса в 7-й магистрале (1.7.3)
		if (campus_num == 9):
			campus_num = ms_num
			ms_num = 7
		vlan = 224 * mgs_num + 32 * ms_num + 4 * campus_num + thread_num + 440
		return vlan;
	else:
		return False
