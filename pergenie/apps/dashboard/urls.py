from django.conf.urls import url

from . import views

app_name = 'apps.dashboard'
urlpatterns = [
    url(r'^$', views.index, name='dashboard'),
]
