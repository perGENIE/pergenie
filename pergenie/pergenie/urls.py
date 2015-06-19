from django.conf.urls import patterns, include, url
from django.conf import settings
from django.conf.urls.static import static

from apps.landing import views as landing_views
from apps.authentication import views as authentication_views
from apps.dashboard import views as dashboard_views


urlpatterns = [
    url(r'^$', landing_views.index, name='index'),
    url(r'^about/$', landing_views.about, name='about'),

    # Authentication
    url(r'^register/$', authentication_views.register),
    url(r'^activation/(?P<activation_key>\w{{{activation_key_length}}})/$'.format(activation_key_length=settings.ACCOUNT_ACTIVATION_KEY_LENGTH),
                        authentication_views.activation),
    url(r'^login/$',    authentication_views.login),
    url(r'^logout/$',   authentication_views.logout),

    # url(r'^trydemo/$',  authentication_views.trydemo),

    # Dashboard
    url(r'^dashboard/$', dashboard_views.index),

    #
    url(r'^upload/$', 'apps.genome.views.index'),
    # url(r'^upload/delete$', 'apps.upload.views.delete'),
    # url(r'^upload/status$', 'apps.upload.views.status'),


    # # 23andme-api
    # url(r'^auth/callback/$', 'apps.api.views.callback'),
    # url(r'^auth/logout/$', 'apps.api.views.logout'),
    # url(r'^auth/profiles/$', 'apps.api.views.profiles'),
    # url(r'^auth/user/$', 'apps.api.views.user'),
    # url(r'^auth/genotype/(?P<snpid>\w+)/$', 'apps.api.views.genotype'),
    # url(r'^login_with_23andme/$', 'apps.login_with_23andme.views.view'),

    # url(r'^riskreport/$', 'apps.riskreport.views.index'),
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

    # url(r'^faq/$', 'apps.faq.views.index'),

    # url(r'^population/$', 'apps.population.views.index'),

    # url(r'^mygene/$', 'apps.mygene.views.index'),
    # url(r'^mygene/(?P<gene>.*?)/$', 'apps.mygene.views.my_gene'),

    # url(r'^mycatalog/$', 'apps.mycatalog.views.index'),

    # url(r'^myprotain/$', 'apps.myprotain.views.index'),
    # url(r'^myprotain/pdb/(?P<pdb_id>[a-zA-Z0-9]{4}?)/$', 'apps.myprotain.views.my_pdb'),

    # url(r'^mydys/$', 'apps.mygene.views.my_dys'),

    # url(r'^traits/$', 'apps.traits.views.index'),
] + static(settings.STATIC_URL)

if settings.DEBUG:
    import debug_toolbar
    from django.contrib import admin
    admin.autodiscover()

    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
        url(r'^admin/', include(admin.site.urls)),
    ]
