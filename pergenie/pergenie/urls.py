from django.conf.urls import patterns, include, url
from django.conf import settings

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

import os
DOCUMENT_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../static')  ###

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'pergenie.views.home', name='home'),
    # url(r'^pergenie/', include('pergenie.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    url(r'^static/(?P<path>.*)$', 'django.views.static.serve',{'document_root': DOCUMENT_ROOT}),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),

    url(r'^auth/callback/$', 'apps.api.views.callback'),
    url(r'^auth/logout/$', 'apps.api.views.logout'),
    url(r'^auth/profiles/$', 'apps.api.views.profiles'),
    url(r'^auth/user/$', 'apps.api.views.user'),
    url(r'^auth/genotype/(?P<snpid>\w+)/$', 'apps.api.views.genotype'),
    url(r'^demo/$', 'apps.demo.views.view'),

    url(r'^$', 'apps.frontend.views.index'),
    url(r'^login/$', 'apps.frontend.views.login'),
    url(r'^login_with_23andme/$', 'apps.frontend.views.login_with_23andme'),
    url(r'^logout/$', 'apps.frontend.views.logout'),
    url(r'^register/$', 'apps.frontend.views.register'),

    url(r'^accounts/', include('registration.backends.default.urls')),
    # registration.backends.default.urls or registration.urls
    # TODO: revise registration settings

    url(r'^dashboard/$', 'apps.dashboard.views.index'),
    url(r'^user_settings/$', 'apps.settings.views.user_settings'),

    url(r'^riskreport/$', 'apps.riskreport.views.index'),
    url(r'^riskreport/show_all/$', 'apps.riskreport.views.show_all'),
    url(r'^riskreport/(?P<trait>[^/]*)/(?P<file_name>[^/]*)/$', 'apps.riskreport.views.trait'),
    url(r'^riskreport/(?P<trait>[^/]*)/(?P<study>[^/]*)/(?P<file_name>[^/]*)/$', 'apps.riskreport.views.study'),

    url(r'^traits/$', 'apps.traits.views.index'),

    url(r'^library/$', 'apps.library.views.index'),
    url(r'^library/trait/$', 'apps.library.views.trait_index'),
    url(r'^library/trait/(?P<trait>.*?)/$', 'apps.library.views.trait'),
    url(r'^library/snps/$', 'apps.library.views.snps_index'),
    url(r'^library/snps/rs(?P<rs>.*?)/$', 'apps.library.views.snps'),
    url(r'^library/summary/$', 'apps.library.views.summary_index'),
    url(r'^library/summary/(?P<field_name>.*?)/$', 'apps.library.views.summary'),

    url(r'^upload/$', 'apps.upload.views.index'),
    url(r'^upload/delete', 'apps.upload.views.delete'),
    url(r'^upload/status', 'apps.upload.views.status'),

    url(r'^faq/$', 'apps.faq.views.index'),
)

if 'rosetta' in settings.INSTALLED_APPS:
    urlpatterns += patterns('',
        url(r'^rosetta/', include('rosetta.urls')),
    )

"""
How Django processes a request
3. Django runs through each URL pattern, in order, and stops at the first one that matches the requested URL.
"""
