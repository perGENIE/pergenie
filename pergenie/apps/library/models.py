from pymongo import MongoClient, ASCENDING, DESCENDING
from django.conf import settings
from lib.mongo.mutate_fasta import MutateFasta


def get_omim_av_records(rs):
    with MongoClient(host=settings.MONGO_URI) as c:
        omim_av = c['pergenie']['omim_av']
        return list(omim_av.find({'rs': rs}).sort('mimNumber'))

def get_seq(chrom, pos):
    m = MutateFasta(settings.PATH_TO_REFERENCE_FASTA)
    seq = m.generate_seq([], offset=[chrom, pos-20 , pos+20])
    return seq
