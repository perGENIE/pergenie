from django.conf.urls import include, url
from django.conf import settings
from django.conf.urls.static import static

from apps.authentication import views as auth_views
from lib.utils import clogging
log = clogging.getColorLogger(__name__)

urlpatterns = []

# Include INSTALLED_APPS urls
apps = list(set(settings.INSTALLED_APPS))
for app in apps:
    if app.startswith('apps.'):
        name = app[5:]
        urlpatterns += [
            url('^{name}/'.format(name=name), include('apps.{name}.urls'.format(name=name))),
        ]

# Root (/)
if 'apps.landing' in apps:
    from apps.landing import views as landing_views
    urlpatterns += [url(r'^$', landing_views.index)]
else:
    log.info('apps.landing is not installed. So /login is set as root (/) url.')
    urlpatterns += [url(r'^$', authentication_views.login)]

# Authentication
urlpatterns += [
    url(r'^logout/$',   auth_views.logout),
    url(r'^trydemo/$',  auth_views.trydemo),
]
if not settings.DEMO_MODE_ONLY:
    urlpatterns += [
        url(r'^register/$', auth_views.register),
        url(r'^about/$',    auth_views.about, name='about'),
        url(r'^activation/(?P<activation_key>\w{{{activation_key_length}}})/$'.format(activation_key_length=settings.ACCOUNT_ACTIVATION_KEY_LENGTH), auth_views.activation),
        url(r'^login/$',    auth_views.login),
    ]

# Static files urls
urlpatterns += static(settings.STATIC_URL)

# Django debug toolbar
if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/$', include(debug_toolbar.urls)),
    ]
