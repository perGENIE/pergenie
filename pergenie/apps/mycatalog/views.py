import sys, os
from pymongo import MongoClient
from django.contrib.auth.decorators import login_required
from django.views.generic.simple import direct_to_template
from django.utils import translation
from django.utils.translation import ugettext as _
from django.conf import settings
from models import *

from lib.api.genomes import Genomes
genomes = Genomes()
from lib.utils.clogging import getColorLogger
log = getColorLogger(__name__)


@login_required
def index(request):
    user_id = request.user.username
    msg, err = '', ''

    with MongoClient(host=settings.MONGO_URI) as c:
        records = list(c['pergenie']['mycatalog'].find())

    # Get genotype_freq & allele_freq for each rs
    for rec in records:
        genotype_freqs, allele_freqs = genomes.get_freq(user_id, rec['rsid'], rec=rec)
        rec['genotype_freq'], rec['allele_freq'] = genotype_freqs[rec['rsid']], allele_freqs[rec['rsid']]

    file_formats = set([x['file_format'] for x in genomes.get_data_infos(user_id)])

    return direct_to_template(request, 'mycatalog/index.html',
                              dict(msg=msg, err=err,
                                   mycatalog=records,
                                   file_formats=file_formats
                                   ))
