from django.conf.urls import include, url
from django.contrib import admin

from . import views

admin.autodiscover()

app_name = 'apps.internal'
urlpatterns = [
    # Health-check
    url(r'^health-check/$', views.health_check),

    # Django admin console
    url(r'^admin/', include(admin.site.urls)),
]
