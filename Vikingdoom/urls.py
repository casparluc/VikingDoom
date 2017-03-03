"""Vikingdoom URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
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
from django.conf.urls import url, include
from django.contrib import admin
from game import views as g_views

urlpatterns = [
    url(r'^$', g_views.index_view, name='home'),
    url(r'^rules/$', g_views.rules_view, name='rules'),
    url(r'^docs/$', g_views.docs_view, name='docs'),
    url(r'^new_player/$', g_views.new_player_view, name='new_player'),
    url(r'^about/$', g_views.about, name='about'),
    url(r'^game/', include('game.urls')),
]
