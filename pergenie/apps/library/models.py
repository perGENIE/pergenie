from pymongo import MongoClient, ASCENDING, DESCENDING
from django.conf import settings


def get_omim_av_records(rs):
    with MongoClient(host=settings.MONGO_URI) as c:
        omim_av = c['pergenie']['omim_av']
        return list(omim_av.find({'rs': rs}).sort('mimNumber'))
