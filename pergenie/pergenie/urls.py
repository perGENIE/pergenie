from django.conf.urls import patterns, include, url
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin

from apps.internal import views as internal_views
from apps.authentication import views as authentication_views
from apps.dashboard import views as dashboard_views
from apps.genome import views as genome_views
from apps.riskreport import views as riskreport_views
from apps.faq import views as faq_views

admin.autodiscover()

urlpatterns = [
    # Internal
    url(r'^internal/admin/', include(admin.site.urls)),
    url(r'^internal/health-check/$', internal_views.health_check),

    # Authentication
    url(r'^register/$', authentication_views.register),
    url(r'^activation/(?P<activation_key>\w{{{activation_key_length}}})/$'.format(activation_key_length=settings.ACCOUNT_ACTIVATION_KEY_LENGTH),
                        authentication_views.activation),
    url(r'^login/$',    authentication_views.login),
    url(r'^logout/$',   authentication_views.logout),
    url(r'^trydemo/$',  authentication_views.trydemo),

    # Dashboard
    url(r'^dashboard/$', dashboard_views.index, name='dashboard'),

    # Genome upload/delete/status
    url(r'^genome/upload/$', genome_views.upload, name='genome-upload'),
    url(r'^genome/delete/$', genome_views.delete, name='genome-delete'),
    url(r'^genome/status/$', genome_views.status, name='genome-status'),

    # Risk Report
    url(r'^riskreport/$', riskreport_views.index, name='riskreport'),
    # url(r'^riskreport/export/$', 'apps.riskreport.views.export'),
    # url(r'^riskreport/show_all/$', 'apps.riskreport.views.show_all'),
    # url(r'^riskreport/show_all_files/$', 'apps.riskreport.views.show_all_files'),
    # url(r'^riskreport/(?P<trait>[^/]*)/$', 'apps.riskreport.views.trait'),
    # url(r'^riskreport/(?P<trait>[^/]*)/(?P<study>[^/]*)/$', 'apps.riskreport.views.study'),

    # url(r'^library/$', 'apps.library.views.index'),
    # url(r'^library/trait/$', 'apps.library.views.trait_index'),
    # url(r'^library/trait/(?P<trait>.*?)/$', 'apps.library.views.trait'),
    # url(r'^library/snps/$', 'apps.library.views.snps_index'),
    # url(r'^library/snps/rs/(?P<rs>.*?)/$', 'apps.library.views.snps'),
    # url(r'^library/summary/$', 'apps.library.views.summary_index'),
    # url(r'^library/summary/(?P<field_name>.*?)/$', 'apps.library.views.summary'),

    # FAQ
    url(r'^faq/$', faq_views.index, name='faq'),

] + static(settings.STATIC_URL)

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [
        url(r'^__debug__/$', include(debug_toolbar.urls)),
    ]

# Include extra apps defined in settings.py
extra_apps = [x for x in list(set(settings.INSTALLED_APPS) - set(settings.DEFAULT_APPS)) if x.startswith('apps.')]

for extra_app in extra_apps:
    name = extra_app[5:]
    urlpatterns += [
        url('^{name}/'.format(name=name), include('apps.{name}.urls'.format(name=name))),
    ]
