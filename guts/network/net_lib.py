from django.core.exceptions import ValidationError
import re

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
        return None

# вычисление концептуальной подсети для нитки
def calculation_subnet(mgs_num, ms_num, campus_num, thread_num):
    if check_concept_ms(ms_num) and check_concept_campus(campus_num) and check_concept_tread(thread_num):
        magic_octet = 225
        magic_octet_2 = 201
        # Проверяем не является ли 9-м в магистрале
        if (campus_num == 9):
            campus_num = ms_num
            ms_num = 7
        
        # сеть
        net=((((4096 * mgs_num) + (512 * ms_num)) + (64 * campus_num))) - 4688
        # собираем ip
        a=10
        tmp=((net + thread_num * 16) / 256)
        
        if mgs_num < 16:
            b = magic_octet
            c = 16 + int(tmp)
        elif mgs_num < 23:
            b = magic_octet_2
            c = -176 + int(tmp);
        d = (net + thread_num * 16)%256
        return "%i.%i.%i.%i/28" % (a, b, c, d)
    else:
        return None

# преобразование интервала в список
def interval_to_arr(interval = ''):
    # например "1-3,5-8,11,14-16" -> [1,2,3,5,6,7,8,11,14,15,16]
    arr = []
    if interval != '':
        for elem_interval in interval.split(','):
            if elem_interval != '':
                petern_interval = "^(([1-9])|([1-9][0-9])|([1-9][0-9][0-9]))|((([1-9])|([1-9][0-9])|([1-9][0-9][0-9]))-(([1-9])|([1-9][0-9])|([1-9][0-9][0-9])))$"
                if re.search(petern_interval, elem_interval) is not None:
                    tmp = elem_interval.split('-')
                    start_interval = tmp[0]
                    if len(tmp)>1:
                        end_interval = tmp[1]
                    else:
                        end_interval = start_interval
                    if start_interval <= end_interval:
                        for i in range(int(start_interval), int(end_interval)+1):
                            if i not in arr:
                                arr.append(i)
                    else:
                        raise ValidationError("ERROR!!!: (%s) Элемент интервала <%s> не корректен!!!" % (interval, elem_interval))
                        return []
                else:
                    raise ValidationError("ERROR!!!: Элемент интервала %s не корректен!!!" % elem_interval)
                    
    return arr

def arr_to_interval(arr = []):
    # процедура, преобразующая числовую последовательность в интервал
    # например [1,2,3,5,6,7,8,11,14,15,16] -> "1-3,5-8,11,14-16"
    if len(arr)>0:
        #arr.sort()
        arr = sorted(arr)
        rezult = str(arr[0])
        start_interval = arr[0]
        for key in range(len(arr)):
            if key == 0:
                continue
            elif arr[key]-arr[key-1]>1:
                if arr[key-1] != start_interval:
                    rezult = "%s-%s,%s" % (rezult, str(arr[key-1]), str(arr[key]))
                else:
                    rezult = "%s,%s" % (rezult, str(arr[key]))
                start_interval = arr[key]
            elif key == len(arr)-1:
                if arr[key]-arr[key-1]>1:
                    if arr[key-1] != start_interval:
                        rezult = "%s-%s,%s" % (rezult, str(arr[key-1]), str(arr[key]))
                    else:
                        rezult = "%s,%s" % (rezult, str(arr[key]))
                else:
                    rezult = rezult + "-" + str(arr[key])
        return rezult
    else:
        return ''

def translit(str):
    translit_dict = {
        'А':'A',
        'Б':'B',
        'В':'V',
        'Г':'G',
        'Д':'D',
        'Е':'E',
        'Ё':'Yo',
        'Ж':'ZH',
        'З':'Z',
        'И':'I',
        'Й':'Y',
        'К':'K',
        'Л':'L',
        'М':'M',
        'Н':'N',
        'О':'O',
        'П':'P',
        'Р':'R',
        'С':'S',
        'Т':'T',
        'У':'U',
        'Ф':'F',
        'Х':'H',
        'Ц':'Ts',
        'Ч':'Ch',
        'Ш':'Sh',
        'Щ':'Ssh',
        'Ъ':'',
        'Ы':'Y',
        'Ь':'',
        'Э':'E',
        'Ю':'Y',
        'Я':'Ya',
        'а':'a',
        'б':'b',
        'в':'v',
        'г':'g',
        'д':'d',
        'е':'e',
        'ё':'yo',
        'ж':'zh',
        'з':'z',
        'и':'i',
        'й':'y',
        'к':'k',
        'л':'l',
        'м':'m',
        'н':'n',
        'о':'o',
        'п':'p',
        'р':'r',
        'с':'s',
        'т':'t',
        'у':'u',
        'ф':'f',
        'х':'h',
        'ц':'ts',
        'ч':'ch',
        'ш':'sh',
        'щ':'ssh',
        'ъ':'',
        'ы':'y',
        'ь':'',
        'э':'e',
        'ю':'y',
        'я':'ya',
        ' ':'_',
        '/':'-',
        ',':'',
        '№':'',
        ',':''
    }
    for char in translit_dict:
        str = str.replace(char, translit_dict[char])
    
    return str
