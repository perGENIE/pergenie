from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.conf import settings


@login_required
def index(request):
    return render(request, 'faq.html',
                  dict())
                  # dict(dbsnp_version=settings.DBSNP_VERSION,
                  #      refgenome_version=settings.REFGENOME_VERSION,
                  #      refgenome_link=settings.REFGENOME_LINK))
