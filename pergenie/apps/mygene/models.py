# -*- coding: utf-8 -*-

import sys, os
from pprint import pformat
from pymongo import MongoClient, ASCENDING, DESCENDING
from django.conf import settings

from lib.mongo.mutate_fasta import MutateFasta

from utils import clogging
log = clogging.getColorLogger(__name__)


# def newline_string(seq, interval=100):
#     result = ''
#     for i,s in enumerate(seq):
#         result += s
#         if i > 0 and i % interval == 0:
#             result += '\n'
#     return result

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

        # get sequence
        m = MutateFasta(settings.PATH_TO_REFERENCE_FASTA)
        records = []
        seq = m.generate_seq(records, offset=[gene_info[u'chrom'],
                                              gene_info[u'txStart'],
                                              gene_info[u'txEnd']])

        gene_info.update({'seq': seq})

        return gene_info
