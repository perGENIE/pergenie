# -*- coding: utf-8 -*-

from pymongo import MongoClient
from django.conf import settings


def get_latest_catalog(port):
    with MongoClient(host=settings.MONGO_URI) as c:
        latest_document = c['pergenie']['catalog_info'].find_one({'status': 'latest'})  # -> {'date': datetime.datetime(2012, 12, 12, 0, 0),}

        if latest_document:
            latest_date = str(latest_document['date'].date()).replace('-', '_')  # -> '2012_12_12'
            catalog = c['pergenie']['catalog'][latest_date]
        else:
            err += 'latest does not exist in catalog_info!'

        # TODO: error handling
        # log.error(err)

        return catalog


def get_traits_infos():
    with MongoClient(host=settings.MONGO_URI) as c:
        trait_info = c['pergenie']['trait_info']

        founds = trait_info.find({})
        traits = set([found['eng'] for found in founds])
        traits_ja = [trait_info.find_one({'eng': trait})['ja'] for trait in traits]
        traits_category = [trait_info.find_one({'eng': trait})['category'] for trait in traits]
        return traits, traits_ja, traits_category
