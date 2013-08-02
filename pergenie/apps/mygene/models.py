import sys, os
from pyfasta import Fasta
from pymongo import MongoClient, ASCENDING, DESCENDING
from django.conf import settings

from lib.mongo.mutate_fasta import MutateFasta
from lib.pdb.get_records import get_records
from lib.utils import clogging
log = clogging.getColorLogger(__name__)


def get_genes():
    with MongoClient(host=settings.MONGO_URI) as c:
        refFlat = c['pergenie']['refFlat']
        genes = [x['gene'] for x in list(refFlat.find())]

        return genes


def get_my_gene(gene):
    with MongoClient(host=settings.MONGO_URI) as c:
        refFlat = c['pergenie']['refFlat']
        gene_info = refFlat.find_one({'gene': gene}) or {}

        if gene_info:
            # get sequence
            m = MutateFasta(settings.PATH_TO_REFERENCE_FASTA)
            records = []
            seq = m.generate_seq(records, offset=[gene_info[u'chrom'],
                                                  gene_info[u'txStart'],
                                                  gene_info[u'txEnd']])
            classed_seq = m.generate_contexted_seq(gene_info)

            gene_info.update({'seq': seq, 'classed_seq': classed_seq})

        return gene_info


def get_atom_records(pdb_id):
    records = []
    record = ''

    ent = get_records(pdb_id)
    if ent:
        for line in ent:
            line = line[0:70]
            line = line.strip('\n ')
            # line = line.replace("'", "")  # FIXME
            assert not '\n' in line
            assert not '"' in line

            if not line.startswith('ATOM') or line.startswith('HETATM'):
                continue
            record += line + '\\n'

            if len(record) > 1000:
                records.append(record)
                record = ''

        records.append(record)

    return records
