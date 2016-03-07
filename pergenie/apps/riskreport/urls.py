from django.conf.urls import url

from . import views

app_name = 'apps.riskreport'
urlpatterns = [
    url(r'^$', views.index, name='riskreport'),
    url(r'^(?P<display_id>[^/]{8})/(?P<phenotype_id>\d*)/$', views.phenotype, name='riskreport-phenotype'),
]
