from pymongo import MongoClient, ASCENDING, DESCENDING
from django.conf import settings
from lib.mongo import search_variants
from lib.mongo.mutate_fasta import MutateFasta


def get_libarary_and_variatns_of_a_trait(trait, user_id):
    with MongoClient(host=settings.MONGO_URI) as c:

        # catalog = get_latest_catalog(port=settings.MONGO_PORT)
        # founds = catalog.find({'trait': trait})

        data_info = c['pergenie']['data_info']
        if user_id.startswith(settings.DEMO_USER_ID): user_id = settings.DEMO_USER_ID

        uploadeds = list(data_info.find({'user_id': user_id}))
        print user_id
        print uploadeds

        file_names = [uploaded['name'] for uploaded in uploadeds]
        file_formats = [uploaded['file_format'] for uploaded in uploadeds]

        variants_maps = {}
        for file_name, file_format in zip(file_names, file_formats):
            library_map, variants_maps[file_name] = search_variants.search_variants(user_id=user_id, file_name=file_name, file_format=file_format,
                                                                                    query=trait, query_type='trait')

        library_list = [library_map[found_id] for found_id in library_map]

        return library_list, variants_maps

def get_omim_av_records(rs):
    with MongoClient(host=settings.MONGO_URI) as c:
        omim_av = c['pergenie']['omim_av']
        return list(omim_av.find({'rs': rs}).sort('mimNumber'))

def get_seq(chrom, pos):
    m = MutateFasta(settings.PATH_TO_REFERENCE_FASTA)
    seq = m.generate_seq([], offset=[chrom, pos-20 , pos+20])
    return seq
