# -*- coding: utf-8 -*-

import sys, os
from pprint import pformat
from pymongo import MongoClient, ASCENDING, DESCENDING
from django.conf import settings
from pyfasta import Fasta
from lib.mongo.mutate_fasta import MutateFasta
from lib.utils.fetch_pdb import fetch_pdb
from lib.utils import clogging
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
        classed_seq = m.generate_contexted_seq(gene_info)

        gene_info.update({'seq': seq, 'classed_seq': classed_seq})

        return gene_info


# def get_dys():
#     records = []
#     fa = Fasta(settings.PATH_TO_REFERENCE_FASTA, key_fn=lambda key: key.split()[0])

#     start = 4330942
#     stop = 4331090
#     seq = fa.sequence({'chr': 'Y', 'start': start, 'stop': stop}, one_based=True)
#     records.append(seq)

#     return records

def pdb2var(pdb_id):
    records = []
    record = ''

    fetch_pdb(pdb_id)
    fin_path = os.path.join('/tmp/atoms', 'pdb'+pdb_id.lower()+'.atom')

    with open(fin_path, 'r') as fin:
        for line in fin:
            line = line[0:70]
            line = line.strip('\n ')
            assert not '\n' in line
            assert not '"' in line
            record += line + '\\n'

            if len(record) > 1000:
                records.append(record)
                record = ''

        records.append(record)

    return records
