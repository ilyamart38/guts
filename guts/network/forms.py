from django import forms

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
import datetime #for checking date range.
from .models import CAMPUS, MS, THREAD, SUBNET, ACCESS_NODE, ACCESS_SWITCH, PORT_OF_ACCESS_SWITCH

class Ms_Form(forms.ModelForm):
    class Meta:
        model = MS
        fields = ('mgs', 'num_in_mgs')

class Campus_Form(forms.ModelForm):
    class Meta:
        model = CAMPUS
        fields = ('prefix', 'ms', 'num_in_ms')

#class Thread_Form(forms.ModelForm):
#    class Meta:
#        model = THREAD
#        fields = ('campus', 'num_in_campus', 'outvlan', 'mapvlan')

class SubnetInThread_Form(forms.ModelForm):
    class Meta:
        model = SUBNET
        fields = ('network', 'thread')

#class Node_Form(forms.ModelForm):
#    class Meta:
#        model = ACCESS_NODE
#        fields = ('address', 'thread')

class New_Access_Switch_Form(forms.ModelForm):
    class Meta:
        model = ACCESS_SWITCH
        fields = ('access_node', 'sw_model', 'ip')

class Ports_Of_Acess_Switch_Form(forms.ModelForm):
    class Meta:
        model = PORT_OF_ACCESS_SWITCH
        fields = (
                'access_switch',
                'num_in_switch', 
                'description', 
                'u_vlan', 
                't_vlans', 
                #'non_pppoe', 
                #'is_signal', 
                #'is_upstream', 
                #'is_bad'
                )

Ports_Of_Acess_Switch_Formset = forms.modelformset_factory(
            PORT_OF_ACCESS_SWITCH,
            fields = (
                'id',
                'port_name',
                'port_type',
                'access_switch',
                'num_in_switch',
                'description', 
                'u_vlan', 
                't_vlans', 
                #'non_pppoe', 
                #'is_signal', 
                #'is_upstream', 
                #'is_bad'
                ),
            extra = 0
            )
        
