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
    with pymongo.MongoClient(host=settings.MONGO_URI) as c:
        db = c['pergenie']
        col = db['population_pca'][scale]

        return [{'position': rec['position'], 'label': rec['popcode']} for rec in col.find()]
