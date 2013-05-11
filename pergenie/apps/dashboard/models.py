from pymongo import MongoClient, ASCENDING, DESCENDING
from django.conf import settings


def get_latest_added_date():
    c = MongoClient(port=settings.MONGO_PORT)
    catalog_stats = c['pergenie']['catalog_stats']

    latest_datetime = list(catalog_stats.find({'field': 'added'}).sort('value', DESCENDING))[0]['value']
    latest_date = latest_datetime.date()

    return latest_date


def get_data_infos(user_id):
    c = MongoClient(port=settings.MONGO_PORT)
    data_info = c['pergenie']['data_info']

    infos = list(data_info.find({'user_id': user_id}))

    return infos
