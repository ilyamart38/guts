from django.conf.urls import url

from . import views

urlpatterns = [
    # адрес главной страницы приложения: /networks/
    url(r'^$',                                             views.IndexView.as_view(),    name='index'),
    # адрес страницы МГС: /network/1/
    url(r'^mgs/(?P<pk>[0-9]+)/$',                          views.MgsView.as_view(),      name='mgs'),
    # адрес для представления кампуса: /network/5/1/
    url(r'^campus/(?P<pk>[0-9]+)/$',                      views.CampusView.as_view(),     name='campus'),
    # адрес для представления нитки: /network/5/1/
    url(r'^thread/(?P<pk>[0-9]+)/$',                      views.ThreadView.as_view(),     name='thread'),
]
