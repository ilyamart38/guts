from django import forms

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
import datetime #for checking date range.
from .models import CAMPUS, MS, THREAD

class Campus_Form(forms.ModelForm):
    class Meta:
        model = CAMPUS
        fields = ('prefix', 'ms', 'num_in_ms')

class Thread_Form(forms.ModelForm):
    class Meta:
        model = THREAD
        fields = ('campus', 'num_in_campus', 'outvlan', 'mapvlan')

