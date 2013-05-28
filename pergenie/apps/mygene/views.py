# -*- coding: utf-8 -*-

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

    return direct_to_template(request, 'mygene/index.html',
                              dict(genes=genes))

@login_required
def my_gene(request, gene):
    user_id = request.user.username
    msg, err = '', ''

    genes = get_genes()

    if not gene in genes:
        raise Http404

    gene_info = get_my_gene(gene)

    return direct_to_template(request, 'mygene/my_gene.html',
                              dict(gene_info=gene_info))
