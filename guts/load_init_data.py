#!/usr/bin/env python
import os
import sys
import xlrd
import re
import ipaddress

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "guts.settings")
try:
    from django.core.management import execute_from_command_line
except ImportError:
    # The above import may fail for some other reason. Ensure that the
    # issue is really that Django is missing to avoid masking other
    # exceptions on Python 2.
    try:
        import django
    except ImportError:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        )
    raise
import django
django.setup()
from network.models import MGS
from network.models import MS
from network.models import SW_MODEL
from network.models import CAMPUS
from network.models import THREAD
from network.models import SUBNET
from network.models import ACCESS_NODE
from network.models import ACCESS_SWITCH


# с помощью скрипта происходит загрузка данных из файла выгрузки из eqm
# файл должен иметь следующую структуру:
# - имя объекта
# - сетевой адрес
# - тип корневого устройства
# - полное имя группы
# - автоопрошенный серийный номер


#процедура для проверки ip адреса на соответствие концептуальным
def check_ip(dev_ip):
    magic_octet = '225'
    magic_octet_2 = '201'
    petern_ip_irk='^10\.%s\.(1[6-9]|[2-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])\.([1-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])' % magic_octet
    petern_ip_ang='^10\.%s\.([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])\.([1-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])' % magic_octet_2
    if re.search(petern_ip_irk, dev_ip)  is None and re.search(petern_ip_ang, dev_ip)  is None:
        return False
    else:
        return True

# процедура преобразования ip в id соответствующего коммутатора    
# соответствие ip-адресов и узлов
def analiz_switch(switch):
    ip = switch['ip']
    if check_ip(ip):
        bld_ids = {
            0:0,
            1:1, 2:1, 3:1,
            4:2, 5:2, 6:2,
            7:3, 8:3, 9:3,
            10:4, 11:4, 12:4, 13:4,
            14:0, 15:0
        }
        # соответствие ip-адресов и номеров коммутаторов в узле
        nums_in_bld = {
            0:0,
            1:1, 2:2, 3:3,
            4:1, 5:2, 6:3,
            7:1, 8:2, 9:3,
            10:1, 11:2, 12:3, 13:4,
            14:0, 15:0
        }
        # 2-й октет
        ip_b = int(ip.split('.')[1])
        # 3-й октет
        ip_c = int(ip.split('.')[2])
        # 4-й октет
        ip_d = int(ip.split('.')[3])
        magic_octet = '225'
        magic_octet_2 = '201'
        petern_ip_irk='^10\.%s\.(1[6-9]|[2-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])\.([1-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])' % magic_octet
        petern_ip_ang='^10\.%s\.([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])\.([1-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])' % magic_octet_2
        if re.search(petern_ip_irk, ip) is not None:
            # мгс
            mgs = int(ip_c/16)
            # мс
            ms = int((ip_c-16*mgs)/2)+1
            # тк
            tk = int(ip_d/64)+4*(ip_c%2)+1
            # нитка
            th = int((ip_d-64*((tk-(ip_c%2)*4)-1))/16)+1
            # номер в нитке
            n_in_th = ip_d-int(ip_d/16)*16

            bld = bld_ids[n_in_th]
            num_in_bld = nums_in_bld[n_in_th]
        elif re.search(petern_ip_ang, ip) is not None:
            # мгс
            mgs = int(ip_c/16)+12
            # мс
            ms = int((ip_c-16*(mgs-16)-64)/2)+1
            # тк
            tk = int(ip_d/64)+4*(ip_c%2)+1
            # нитка
            th = int((ip_d-64*((tk-(ip_c%2)*4)-1))/16)+1
            # номер в нитке
            n_in_th = ip_d-int(ip_d/16)*16

            bld = bld_ids[n_in_th]
            num_in_bld = nums_in_bld[n_in_th]
        else:
            return 'IP IS BAD!'
        if ms == 7 and tk in range(1,7):
            ms = tk
            tk = 9
        komm_id = mgs*100000+ms*10000+tk*1000+th*100+bld*10+num_in_bld
        if komm_id > 100000:
            #все манипуляции с базой делаем только в случае если ip коммутатор отсутстыует в базе!
            if not ACCESS_SWITCH.objects.filter(ip=switch['ip']):
#                print(switch['ip'])
                if MGS.objects.filter(mgs_num = mgs):
                    sw_mgs = MGS.objects.get(mgs_num = mgs)
                    if not MS.objects.filter(mgs=sw_mgs, num_in_mgs=ms):
                        print('Не обнаружена МС-%s.%s!!!' % (mgs, ms))
                        sw_ms = MS(mgs=sw_mgs, num_in_mgs=ms)
                        sw_ms.save()
                        print('Сздан объект %s!' % sw_ms)
    #                else:
    #                    print('МС-%s.%s обнаружена!' % (mgs, ms))
                    # проверяем наличие кампуса соответствующего ip коммутатора
                    if MS.objects.filter(mgs=sw_mgs, num_in_mgs=ms):
                        sw_ms = MS.objects.get(mgs=sw_mgs, num_in_mgs=ms)
                        # В случае соответствия названия группы eqm с концепцией, создаем ППК, в противном случае создаем МКУ
                        if switch['group'].find('ППК - %s.%s.%s' % (mgs, ms, tk)) >= 0:
                            if not CAMPUS.objects.filter(ms=sw_ms, num_in_ms = tk):
                                print('Будет создан ППК')
                                print('Необнаружен кампус %s.%s.%s' % (mgs, ms, tk))
                                sw_campus = CAMPUS(ms=sw_ms, num_in_ms=tk)
                                sw_campus.save()
                                print('Сздан объект %s!' % sw_campus)
                            else:
                                sw_campus = CAMPUS.objects.get(ms=sw_ms, num_in_ms = tk)
                        else:
                            if not CAMPUS.objects.filter(ms=sw_ms, num_in_ms = tk):
                                print('Будет создан МКУ')
                                print('Необнаружен кампус %s.%s.%s' % (mgs, ms, tk))
                                sw_campus = CAMPUS(prefix='mku', ms=sw_ms, num_in_ms=tk)
                                sw_campus.save()
                                print('Сздан объект %s!' % sw_campus)
                            else:
                                sw_campus = CAMPUS.objects.get(ms=sw_ms, num_in_ms = tk)
                        # Вычисляем адрес узла с которого включен коммутутор
                        if len(switch['name'].split(',')) > 2:
                            # выделяем последния два поля (из разделенных запятой)
                            address = '%s, %s' % (switch['name'].split(',')[-2], re.sub(switch['ip'], '', switch['name'].split(',')[-1]).strip())
                            # Вычисляем подсеть к которой пренадлежит ip коммутатора
                            sw_net = ipaddress.ip_interface('%s/28' % switch['ip']).network
                            # проверяем существование данной подсети
                            if SUBNET.objects.filter(network=sw_net):
                                sw_subnet = SUBNET.objects.get(network=sw_net)
                                if sw_subnet.gw == '0.0.0.0':
                                    sw_subnet.gw = sw_subnet.gw_address()
                                    sw_subnet.save()
                                    print('У подсети %s задан шлюз %s' % (sw_subnet, sw_subnet.gw))
                                #Проверяем есть ли узел с адресом коммутатора в нитке которой пренадлежит подсеть
                                if not ACCESS_NODE.objects.filter(address=address, thread=sw_subnet.thread):
                                    print('Узел с адресом <%s> не обнаружен!' % address)
                                    sw_node = ACCESS_NODE(address=address, thread=sw_subnet.thread)
                                    sw_node.save()
                                    print('Создан объект <%s>' % sw_node)
                                    if not ACCESS_SWITCH.objects.filter(ip=switch['ip'], access_node=sw_node):
                                        sw=ACCESS_SWITCH(ip=switch['ip'], access_node=sw_node)
                                        sw.save()
                                        print('Создан объект <%s>' % sw)
                                else:
                                    sw_node = ACCESS_NODE.objects.get(address=address, thread=sw_subnet.thread)
                                    if not ACCESS_SWITCH.objects.filter(ip=switch['ip'], access_node=sw_node):
                                        sw=ACCESS_SWITCH(ip=switch['ip'], access_node=sw_node)
                                        sw.save()
                                        print('Создан объект <%s>' % sw)
                                
                            else:
                                print('Не обнаружена подсет %s' % sw_net)
                                # Если коммутатор в МКУ то создадим нужную подсеть в 1-й нитке МКУ
                                if sw_campus.prefix == 'mku':
                                    if THREAD.objects.filter(campus=sw_campus):
                                        sw_thread = THREAD.objects.get(campus=sw_campus, num_in_campus=1)
                                        sw_subnet = SUBNET(thread=sw_thread, network=sw_net)
                                        sw_subnet.gw = sw_subnet.gw_address()
                                        sw_subnet.save()
                                        print('Создан объект <%s>' % sw_subnet)
                                        #Проверяем есть ли узел с адресом коммутатора в нитке которой пренадлежит подсеть
                                        if not ACCESS_NODE.objects.filter(address=address, thread=sw_subnet.thread):
                                            print('Узел с адресом <%s> не обнаружен!' % address)
                                            sw_node = ACCESS_NODE(address=address, thread=sw_subnet.thread)
                                            sw_node.save()
                                            print('Создан объект <%s>' % sw_node)
                                            if not ACCESS_SWITCH.objects.filter(ip=switch['ip'], access_node=sw_node):
                                                sw=ACCESS_SWITCH(ip=switch['ip'], access_node=sw_node)
                                                sw.save()
                                                print('Создан объект <%s>' % sw)
                                        else:
                                            sw_node = ACCESS_NODE.objects.get(address=address, thread=sw_subnet.thread)
                                            if not ACCESS_SWITCH.objects.filter(ip=switch['ip'], access_node=sw_node):
                                                sw=ACCESS_SWITCH(ip=switch['ip'], access_node=sw_node)
                                                sw.save()
                                                print('Создан объект <%s>' % sw)
                                        
                                    else:
                                        print('Нет ниток в %s!' % sw_campus)
                                        print('address: ', address)
                                        print('sw_net: ', sw_net)
                                        print('sw_campus: ', sw_campus)
                                        sys.exit()
                                else:
                                    print('NEOK!')
                                    print('address: ', address)
                                    print('sw_net: ', sw_net)
                                    print('sw_campus: ', sw_campus)
                                    sys.exit()
                        else:
                            address = '???'
            else:
                sw = ACCESS_SWITCH.objects.get(ip=switch['ip'])
                set_model_sw(sw,switch['type'])
            
            return str(komm_id)
        else:
            return 'BAD ID <'+komm_id+'>'
    else:
        print('IP <%s> IS BAD!' % ip)
        return

def set_model_sw(access_switch, model):
    if len(model.split(' >> ')) == 2:
        model = model.split(' >> ')[1]
        if model != '' and SW_MODEL.objects.filter(eqm_type=model).count()==1:
            sw_model = SW_MODEL.objects.get(eqm_type=model)
            if access_switch.sw_model != sw_model:
                access_switch.sw_model = sw_model
                access_switch.save()
                print('Модель коммутатора %s обновлена на %s' % (access_switch, access_switch.sw_model))
        else:
            print('Неизвестная модель коммутатора: %s' % model)
            #sys.exit()
    else:
        print('Непонятный тип коммутатора: %s' % model)
        sys.exit()

if __name__ == "__main__":
###########################################################################33
    #Загружаем данные о коммутаторах
    file = './initial_data/access_switches.xls'
    rb = xlrd.open_workbook(file)
    sheet = rb.sheet_by_index(0)
    switchs = []
    for row in range(1,sheet.nrows):
        switch = {}
        switch['name'] = sheet.row_values(row)[0]
        switch['ip'] = sheet.row_values(row)[1]
        switch['type'] = sheet.row_values(row)[2]
        switch['group'] = sheet.row_values(row)[3]
        switch['sn'] = sheet.row_values(row)[4]
        switch['campus'] = None
        switchs.append(switch)
    #print(switchs[0])

    # Проверяем наличие всех МГС в базе
    mgss = []
    for switch in switchs:
        if len(switch['group'].split(' -> ')) > 3:
            # в названии группы должно иметься поле вида МГС-01 или МУП-01
            # в котором после знака '-' следует номер МГС
            # находим первое поле в котором встречается МГС или МУП
            switch['mgs'] = ''
            for field in switch['group'].split(' -> '):
                if field.find('МГС') >= 0:
                    # в поле могут быть разные комментарии через пробел
                    for element in field.split(' '):
                        if element.find('МГС') >= 0:
                            switch['mgs'] = element.split('-')[1]
                            break
                    break
                elif field.find('МУП') >= 0:
                    # в поле могут быть разные комментарии через пробел
                    for element in field.split(' '):
                        if element.find('МУП') >= 0:
                            switch['mgs'] = element.split('-')[1]
                            break
                    break
            if switch['mgs'] == '':
                print('МГС не найдена: <%s>' % switch['group'])
                break
            if switch['mgs'] not in mgss:
                mgss.append(switch['mgs'])
    # Проверяем наличие полученных номеров МГС в базе
    # недостающие создаем
    for mgs in mgss:
        mgs_num = int(mgs)
        if MGS.objects.filter(mgs_num=mgs_num):
            #print('%s - OK' % mgs)
            pass
        else:
            print('%s - NE OK!!!' % mgs)
            # Создаем недостающую МГС
            new_mgs = MGS(
                mgs_num = mgs_num,
                address = '???',
                )
            new_mgs.save()
            print('Создан объект %s' % new_mgs)
    
    # из ip адресов коммутаторов вычисляем номера магистралей и добавляем недостающие в базу
    for switch in switchs:
        if switch['ip']:
            analiz_switch(switch)
        else:
            print(switch)
            print('ip не задан!')
            break
#        break
