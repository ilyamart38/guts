from django.conf.urls import url

from . import views

urlpatterns = [
    # адрес главной страницы приложения: /clients/
    url(r'^$',                                             views.IndexView.as_view(),    name='index'),
]
