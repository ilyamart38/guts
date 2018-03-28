from django.conf.urls import url

from . import views

urlpatterns = [
    # адрес главной страницы приложения: /networks/
    url(r'^$',                                                                              views.IndexView.as_view(),          name='network_index'),
    
    # адрес страницы МГС: /network/1/
    url(r'^mgs/(?P<pk>[0-9]+)/$',                                                           views.MgsView.as_view(),            name='mgs'),
    # адрес для добавления кампуса в МС: /network/mgs/1/1/new_campus
    url(r'^mgs/(?P<mgs_id>[0-9]+)/(?P<ms_id>[0-9]+)/new_campus/$',                          views.NewCampusInMs,                name='new_campus_in_ms'),
    # адрес для добавления магистрали в МГС: /network/mgs/1/new_ms
    url(r'^mgs/(?P<mgs_id>[0-9]+)/new_ms/$',                                                views.NewMsInMgs,                   name='new_ms_in_mgs'),
    # адрес для удаления магистрали: /network/ms/1/delete/
    url(r'^ms/(?P<pk>[0-9]+)/delete/$',                                                     views.MsDelete.as_view(),           name='ms_delete'),

    # адрес для представления кампуса: /network/campus/1/
    url(r'^campus/(?P<pk>[0-9]+)/$',                                                        views.CampusView.as_view(),         name='campus'),
    # адрес для создания кампуса: /network/campus/1/
    url(r'^campus/create/$',                                                                views.CampusCreate.as_view(),       name='campus_create'),
    # адрес для редактирования кампуса в МГС: /network/campus/1/edit
    url(r'^campus/(?P<pk>[0-9]+)/edit/$',                                                   views.CampusUpdate.as_view(),       name='campus_edit'),
    # адрес для удаления кампуса: /network/campus/1/delete/
    url(r'^campus/(?P<pk>[0-9]+)/delete/$',                                                 views.CampusDelete.as_view(),       name='campus_delete'),
    
    # адрес для представления нитки: /network/5/1/
    url(r'^thread/(?P<pk>[0-9]+)/$',                                                        views.ThreadView.as_view(),         name='thread'),
    # адрес для редактирования нитки: /network/thread/1/edit
    url(r'^thread/(?P<pk>[0-9]+)/edit/$',                                                   views.ThreadUpdate.as_view(),       name='thread_edit'),
    # адрес для удаления кампуса: /network/thread/1/delete/
    url(r'^thread/(?P<pk>[0-9]+)/delete/$',                                                 views.ThreadDelete.as_view(),       name='thread_delete'),
    # адрес для добавления нитки в кампусе: /network/campus/1/new_thread
    url(r'^campus/(?P<campus_id>[0-9]+)/new_thread/$',                                      views.NewThreadInCampus,            name='new_thread_in_campus'),
]
