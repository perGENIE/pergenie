# from django.db import models
from django.conf import settings
import pymongo

import sys


def get_pca_snps():
    """Get PCA SNPs of each scale.
    """
    pass


def get_genotypes(snps):
    """Get genotyes of username.filename.
    """
    pass


def project_new_person(genotyes, scale):
    """Project new person onto PCA coordinate.

    args:
    retval:
    """
    pass


def get_people(scale):
    """Get points of people in PCA coordinate.

    args: str(scale)
    retval: list(list(), ...)
    """
    popcode2global = {'CHB': 'EastAsia', 'JPT': 'EastAsia', 'CHS': 'EastAsia',
                      'CEU': 'Europe', 'TSI': 'Europe', 'GBR': 'Europe', 'FIN': 'Europe', 'IBS': 'Europe',
                      'YRI': 'Africa', 'LWK': 'Africa', 'ASW': 'Africa',
                      'MXL': 'Americas', 'CLM': 'Americas', 'PUR': 'Americas'}

    with pymongo.MongoClient(host=settings.MONGO_URI) as c:
        db = c['pergenie']
        col = db['population_pca'][scale]

        if scale == 'global':
            records = [{'position': rec['position'],
                        'label': popcode2global[rec['popcode']],
                        'map_label': rec['popcode']} for rec in col.find()]
        else:
            records = [{'position': rec['position'],
                        'label': rec['popcode'],
                        'map_label': rec['popcode']} for rec in col.find()]

        return records
