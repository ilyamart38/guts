from django.conf.urls import url

from . import views

urlpatterns = [
    # адрес главной страницы приложения: /ipoe/
    url(r'^$',                                             views.IndexView.as_view(),    name='index'),
]
