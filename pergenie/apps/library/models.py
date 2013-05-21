from pymongo import MongoClient
# from lib.mongo.get_latest_catalog import get_latest_catalog
from django.conf import settings
from lib.mongo import search_variants


def get_latest_catalog_date():
    c = MongoClient(host=settings.MONGO_URI)
    catalog_info = c['pergenie']['catalog_info']
    latest_catalog_date = catalog_info.find_one({'status': 'latest'})['date']

    return latest_catalog_date


def get_libarary_and_variatns_of_a_trait(trait, user_id):
    c = MongoClient(host=settings.MONGO_URI)

    # catalog = get_latest_catalog(port=settings.MONGO_PORT)
    # founds = catalog.find({'trait': trait})

    data_info = c['pergenie']['data_info']

    uploadeds = list(data_info.find({'user_id': user_id}))
    file_names = [uploaded['name'] for uploaded in uploadeds]
    file_formats = [uploaded['file_format'] for uploaded in uploadeds]

    variants_maps = {}
    for file_name, file_format in zip(file_names, file_formats):
        library_map, variants_maps[file_name] = search_variants.search_variants(user_id=user_id, file_name=file_name, file_format=file_format,
                                                                                query=trait, query_type='trait')

    library_list = [library_map[found_id] for found_id in library_map]

    return library_list, variants_maps
