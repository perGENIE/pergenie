# -*- coding: utf-8 -*-

import sys, os
from pprint import pformat
from pymongo import MongoClient, ASCENDING, DESCENDING

from django.conf import settings

from utils import clogging
log = clogging.getColorLogger(__name__)


# FIXME: replace refFlat.find() to GENES
def get_genes():
    with MongoClient(host=settings.MONGO_URI) as c:
        refFlat = c['pergenie']['refFlat']
        genes = [x['gene'] for x in list(refFlat.find())]

        return genes

def get_my_gene(gene):
    with MongoClient(host=settings.MONGO_URI) as c:
        refFlat = c['pergenie']['refFlat']
        gene_info = refFlat.find_one({'gene': gene})

        return gene_info
