from django.conf.urls import patterns, include, url
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

    url(r'^$', 'apps.frontend.views.index'),
    url(r'^login/$', 'apps.frontend.views.login'),
    url(r'^logout/$', 'apps.frontend.views.logout'),
    url(r'^register/$', 'apps.frontend.views.register'),

    # Activation
    url(r'^activation/(?P<activation_key>\w+)/$', 'apps.frontend.views.activation'),
    # or [a-fA-F0-9]{40}

    url(r'^dashboard/$', 'apps.dashboard.views.index'),
    url(r'^settings/$', 'apps.settings.views.settings'),

    url(r'^riskreport/$', 'apps.riskreport.views.index'),
    url(r'^riskreport/(?P<file_name>[^/]*)/(?P<trait>[^/]*)/$', 'apps.riskreport.views.trait'),
    url(r'^riskreport/(?P<file_name>[^/]*)/(?P<trait>[^/]*)/(?P<study_name>[^/]*)/$', 'apps.riskreport.views.study'),

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

    url(r'^tutorial/$', 'apps.tutorial.views.index'),
    url(r'^tutorial/personal$', 'apps.tutorial.views.personal'),
    url(r'^tutorial/institution$', 'apps.tutorial.views.institution'),
)


"""
How Django processes a request
3. Django runs through each URL pattern, in order, and stops at the first one that matches the requested URL.
"""
