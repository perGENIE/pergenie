from pymongo import MongoClient, ASCENDING, DESCENDING
from django.conf import settings
from lib.mongo.get_latest_catalog import get_latest_catalog

def get_latest_added_date():
    c = MongoClient(port=settings.MONGO_PORT)
    catalog_stats = c['pergenie']['catalog_stats']

    # NOTE: If catalog is under importing, this date may not be correct. But it's ok.
    latest_datetime = list(catalog_stats.find({'field': 'added'}).sort('value', DESCENDING))[0]['value']
    latest_date = latest_datetime.date()

    return latest_date


def get_data_infos(user_id):
    c = MongoClient(port=settings.MONGO_PORT)
    data_info = c['pergenie']['data_info']

    infos = list(data_info.find({'user_id': user_id}))

    return infos


def get_recent_catalog_records():
    catalog = get_latest_catalog(port=settings.MONGO_PORT)

    recent_date = list(catalog.find().sort('added', DESCENDING))[0]['added']
    recent_records = list(catalog.find({'added': recent_date}))

    uniq_studies, uniq_ids = list(), set()
    for record in recent_records:
        if not record['pubmed_id'] in uniq_ids:
            uniq_studies.append(record)
            uniq_ids.update([record['pubmed_id']])

            # limit to 3 studies
            if len(uniq_ids) == 3:
                break

    for record in uniq_studies:
        print record['added']

    return uniq_studies
