from django.conf.urls import url

from . import views

urlpatterns = [
    # ex: /networks/
    url(r'^$', views.index, name='index'),
    # ex: /network/1/
    url(r'^(?P<mgs_id>[0-9]+)/$', views.mgs_view, name='mgs'),
    # ex: /network/5/1/
    url(r'^(?P<mgs_id>[0-9]+)/(?P<campus_id>[0-9]+)/$', views.campus_view, name='campus'),

]
