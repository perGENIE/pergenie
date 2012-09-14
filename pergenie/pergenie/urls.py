from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'pergenie.views.home', name='home'),
    # url(r'^pergenie/', include('pergenie.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),

    url(r'^$', 'frontend.views.index'),
    url(r'^login/$', 'frontend.views.login'),
    url(r'^logout/$', 'frontend.views.logout'),
    url(r'^register/$', 'frontend.views.register'),
    url(r'^about/$', 'frontend.views.about'),

    url(r'^dashboard/$', 'dashboard.views.index'),

    url(r'^riskreport/$', 'riskreport.views.index'),

    url(r'^catalog/$', 'catalog.views.index'),

    url(r'^upload/$', 'upload.views.index'),
)
