from django.conf.urls import url

from . import views

app_name = 'apps.genome'
urlpatterns = [
    # Genome upload/delete/status
    url(r'^upload/$', views.upload, name='genome-upload'),
    url(r'^delete/$', views.delete, name='genome-delete'),
    url(r'^status/$', views.status, name='genome-status'),
]
