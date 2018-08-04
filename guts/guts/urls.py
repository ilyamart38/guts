"""guts URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import RedirectView

from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    url(r'^$',         RedirectView.as_view(url='/network/')),
    url(r'^admin/',    admin.site.urls),
    url(r'^accounts/', include('registration.urls')),
    url(r'^network/',  include('network.urls'), name='network'),
    url(r'^clients/',  include('clients.urls'), name='clients'),
    url(r'^ipoe/',     include('ipoe.urls'),    name='ipoe'),
    url(r'^l2/',       include('l2.urls'),      name='l2'),
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += [
    url(r'^accounts/', include('django.contrib.auth.urls')),
]
