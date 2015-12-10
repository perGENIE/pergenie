from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.authentication.models import User
from apps.genome.models import Genome
from apps.gwascatalog.models import GwasCatalogSnp
from utils.clogging import getColorLogger
log = getColorLogger(__name__)


@login_required
def index(request):
    while True:
        # Your Genome Files
        user = User.objects.filter(id=request.user.id)
        owner_genomes = Genome.objects.filter(owner=user)
        reader_genomes = Genome.objects.filter(readers__in=user)
        my_genomes = list(owner_genomes) + list(reader_genomes)

        # Recently Added Studies
        recent_studies = GwasCatalogSnp.objects.distinct('pubmed_id', 'date_published').order_by('-date_published')[0:3]

        break

    return render(request, 'dashboard.html',
                  dict(my_genomes=my_genomes,
                       recent_studies=recent_studies))
