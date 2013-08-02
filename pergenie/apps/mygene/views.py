from django.contrib.auth.decorators import login_required
from django.views.generic.simple import direct_to_template
from django.http import Http404
from django.utils.translation import ugettext as _
from django.conf import settings
from apps.riskreport.forms import RiskReportForm

import sys, os
import pymongo

from lib.mongo.get_latest_catalog import get_latest_catalog
from lib.mongo.get_traits_infos import get_traits_infos
from models import *

from utils import clogging
log = clogging.getColorLogger(__name__)


@login_required
def index(request):
    user_id = request.user.username
    msg, err = '', ''

    genes = get_genes()
    if genes:
        genes = genes[0:20]  # FIXME

    return direct_to_template(request, 'mygene/index.html',
                              dict(genes=genes))


@login_required
def my_gene(request, gene):
    user_id = request.user.username
    msg, err = '', ''

    # genes = get_genes()
    # if not gene in genes:
    #     raise Http404

    # Gene
    gene_info = get_my_gene(gene)

    # Protein
    pdb_id = '101m'  # TODO: get_pdb(gene)
    pdb_records = get_atom_records(pdb_id)

    return direct_to_template(request, 'mygene/my_gene.html',
                              dict(gene_info=gene_info,
                                   pdb_records=pdb_records,
                                   pdb_name=pdb_id.upper()))
