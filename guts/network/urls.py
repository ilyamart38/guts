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
    # адрес для добавления нитки в кампусе: /network/campus/1/new_thread
    url(r'^campus/(?P<campus_id>[0-9]+)/new_thread/$',                                      views.NewThreadInCampus,            name='new_thread_in_campus'),
    # адрес для редактирования нитки: /network/thread/1/edit
    url(r'^thread/(?P<pk>[0-9]+)/edit/$',                                                   views.ThreadUpdate.as_view(),       name='thread_edit'),
    # адрес для удаления нитки: /network/thread/1/delete/
    url(r'^thread/(?P<pk>[0-9]+)/delete/$',                                                 views.ThreadDelete.as_view(),       name='thread_delete'),

    # адрес для представления подсети: /network/subnet/1/
    url(r'^subnetnet/(?P<pk>[0-9]+)/$',                                                     views.SubnetView.as_view(),         name='subnet'),
    # адрес для добавления подсети в нитку: /network/thread/1/new_net
    url(r'^thread/(?P<thread_id>[0-9]+)/new_net/$',                                         views.SubnetInThread,               name='new_net_in_thread'),
    # адрес для удаления подсети: /network/subnet/1/delete/
    url(r'^subnet/(?P<pk>[0-9]+)/delete/$',                                                 views.SubnetDelete.as_view(),       name='subnet_delete'),

    # адрес для добавления узла в нитку: /network/thread/1/new_node
    url(r'^thread/(?P<thread_id>[0-9]+)/new_access_node/$',                                 views.NewAccessNodeInThread,            name='new_access_node_in_thread'),
    # адрес для редактирования узла доступа: /network/access_node/1/edit
    url(r'^access_node/(?P<pk>[0-9]+)/edit/$',                                              views.AccessNodeUpdate.as_view(),       name='access_node_edit'),
    # адрес для удаления узла доступа: /network/access_node/1/delete/
    url(r'^access_node/(?P<pk>[0-9]+)/delete/$',                                            views.AccessNodeDelete.as_view(),       name='access_node_delete'),

    # адрес для добавления коммутатора в ноду: /network/access_node/1/new_access_switch
    url(r'^access_node/(?P<access_node_id>[0-9]+)/new_access_switch/$',                     views.NewAccessSwitchInNode,            name='new_access_switch_in_node'),
    # адрес для представления коммутатора доступа: /access_switch/5/
    url(r'^access_switch/(?P<pk>[0-9]+)/$',                                                 views.AccessSwitchView.as_view(),         name='access_switch'),
    # адрес для удаления коммутатора доступа: /network/access_switch/1/delete/
    url(r'^access_switch/(?P<pk>[0-9]+)/delete/$',                                            views.AccessSwitchDelete.as_view(),       name='access_switch_delete'),
    # адрес для изменения модели коммутатора доступа: /network/access_switch/1/change_model/
    url(r'^access_switch/(?P<pk>[0-9]+)/change_model/$',                                            views.AccessSwitchModel.as_view(),       name='access_switch_mdoel'),

    ]
