from django.contrib.auth.decorators import login_required
from django.views.generic.simple import direct_to_template
from django.conf import settings

@login_required
def index(request):
    return direct_to_template(request, 'faq/index.html',
                              dict(dbsnp_version=settings.DBSNP_VERSION,
                                   refgenome_version=settings.REFGENOME_VERSION,
                                   refgenome_link=settings.REFGENOME_LINK))
