from django.conf.urls import url
from django.contrib import admin

from . import views

admin.autodiscover()

app_name = 'apps.internal'
urlpatterns = [
    # Health-check
    url(r'^internal/health-check/$', internal_views.health_check),

    # Django admin console
    url(r'^internal/admin/', include(admin.site.urls)),
]
