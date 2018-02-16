from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, Http404

from .models import MGS

def index(request):
    mgs_list = MGS.objects.order_by('Title')
    context = {'mgs_list': mgs_list}
    template = 'network/index.html'
    return render(request, template, context)
    

def mgs_view(request, mgs_id):
    mgs = get_object_or_404(MGS, pk=mgs_id)
    return render(request, 'network/mgs.html', {'mgs': mgs})


def campus_view(request, mgs_id, campus_id):
    response = "Кампус_id %s."
    return HttpResponse(response % campus_id)
