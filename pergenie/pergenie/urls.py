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
from lib.utils import clogging
log = clogging.getColorLogger(__name__)

admin.autodiscover()

urlpatterns = [
    # Internal
    url(r'^internal/admin/', include(admin.site.urls)),
    url(r'^internal/health-check/$', internal_views.health_check),

    # Authentication
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
    url(r'^riskreport/(?P<display_id>[^/]{8})/(?P<phenotype_id>\d*)/$', riskreport_views.phenotype, name='riskreport-phenotype'),
    # TODO:
    # url(r'^riskreport/(?P<display_id>[^/]{8})/$', 'apps.riskreport.views.show', name='riskreport-show'),
    # url(r'^riskreport/export/$', 'apps.riskreport.views.export'),

    # TODO:
    # url(r'^library/$', 'apps.library.views.index'),
    # url(r'^library/trait/$', 'apps.library.views.trait_index'),
    # url(r'^library/trait/(?P<trait>.*?)/$', 'apps.library.views.trait'),
    # url(r'^library/snps/$', 'apps.library.views.snps_index'),
    # url(r'^library/snps/rs/(?P<rs>.*?)/$', 'apps.library.views.snps'),
    # url(r'^library/summary/$', 'apps.library.views.summary_index'),
    # url(r'^library/summary/(?P<field_name>.*?)/$', 'apps.library.views.summary'),

    # FAQ
    # url(r'^faq/$', faq_views.index, name='faq'),

] + static(settings.STATIC_URL)

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [
        url(r'^__debug__/$', include(debug_toolbar.urls)),
    ]

if not settings.DEMO_MODE_ONLY:
    urlpatterns += [
        url(r'^register/$', authentication_views.register),
        url(r'^about/$',    authentication_views.about, name='about'),
        url(r'^activation/(?P<activation_key>\w{{{activation_key_length}}})/$'.format(activation_key_length=settings.ACCOUNT_ACTIVATION_KEY_LENGTH),
            authentication_views.activation),
        url(r'^login/$',    authentication_views.login),
    ]

# Include extra apps defined in settings.py
extra_apps = [x for x in list(set(settings.INSTALLED_APPS) - set(settings.DEFAULT_APPS)) if x.startswith('apps.')]

for extra_app in extra_apps:
    name = extra_app[5:]
    urlpatterns += [
        url('^{name}/'.format(name=name), include('apps.{name}.urls'.format(name=name))),
    ]

# Set root (/)
if 'apps.landing' in extra_apps:
    from apps.landing import views as landing_views
    root_view = landing_views.index
else:
    log.info('apps.landing is not installed. So /login is set as root (/) url.')
    root_view = authentication_views.login

urlpatterns += [
    url(r'^$', root_view),
]
