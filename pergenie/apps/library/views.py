# -*- coding: utf-8 -*-
import os

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.generic.simple import direct_to_template
from django.utils.translation import get_language
from django.utils.translation import ugettext as _
from django.conf import settings

from apps.library.forms import LibraryForm

import pymongo

from lib.mongo import search_variants
from lib.mongo import search_catalog
from utils.io import pickle_load_obj
from utils import clogging
log = clogging.getColorLogger(__name__)

MY_TRAIT_LIST = pickle_load_obj(os.path.join(settings.CATALOG_SUMMARY_CACHE_DIR, 'trait_list.p'))
MY_TRAIT_LIST_JA = pickle_load_obj(os.path.join(settings.CATALOG_SUMMARY_CACHE_DIR, 'trait_list_ja.p'))


@require_http_methods(['GET', 'POST'])
@login_required
def index(request):
    user_id = request.user.username
    err = ''
    msgs = {}

    msgs['dbsnp_version'] = settings.DBSNP_VERSION
    msgs['refgenome_version'] = settings.REFGENOME_VERSION

    if request.method == 'POST':
        # if query:
        with pymongo.Connection(port=settings.MONGO_PORT) as connection:
            db = connection['pergenie']
            data_info = db['data_info']

            uploadeds = list(data_info.find({'user_id': user_id}))
            file_name = uploadeds[0]['name']

            query = '"{}"'.format(LibraryForm.query)
            catalog_map, variants_map = search_variants.search_variants(user_id, file_name, query)
            catalog_list = [catalog_map[found_id] for found_id in catalog_map]  # somehow catalog_map.found_id does not work in templete...

            return direct_to_template(request,
                                      'library_trait.html',
                                      {'err': err,
                                       'trait_name': query,
                                       'catalog_list': catalog_list,
                                       'variants_map': variants_map})

    msgs['err'] = err
    msgs['my_trait_list'] = MY_TRAIT_LIST
    msgs['my_trait_list_ja'] = MY_TRAIT_LIST_JA

    return direct_to_template(request, 'library.html', msgs)


@login_required
def summary_index(request):
    err = ''

    # TODO: error handling ?
    catalog_summary = pickle_load_obj(os.path.join(settings.CATALOG_SUMMARY_CACHE_DIR, 'catalog_summary.p'))
    field_names = pickle_load_obj(os.path.join(settings.CATALOG_SUMMARY_CACHE_DIR, 'field_names.p'))

    catalog_uniqs_counts = {}

    for field_name in field_names:
        uniqs = catalog_summary.get(field_name[0])

        if uniqs:
            catalog_uniqs_counts[field_name] = len(uniqs)

    log.debug('catalog_uniqs_counts', catalog_uniqs_counts)

    return direct_to_template(request, 'library_summary_index.html',
                              {'err': err,
                               'catalog_uniqs_counts': catalog_uniqs_counts})


@login_required
def summary(request, field_name):
    err = ''

    catalog_summary = pickle_load_obj(os.path.join(settings.CATALOG_SUMMARY_CACHE_DIR, 'catalog_summary.p'))
    uniqs_counts = catalog_summary.get(field_name)

    # TODO: 404?
    if not uniqs_counts:
        err = 'not found'
        uniqs_counts = {}

    return direct_to_template(request, 'library_summary.html',
                              {'err': err,
                               'uniqs_counts': uniqs_counts,
                               'field_name': field_name})


@login_required
def trait_index(request):
    err = ''

    return direct_to_template(request,
                              'library_trait_index.html',
                              {'err': err,
                               'my_trait_list': MY_TRAIT_LIST,
                               'my_trait_list_ja': MY_TRAIT_LIST_JA,
                               })


@login_required
def trait(request, trait):
    user_id = request.user.username
    err = ''

    query = trait.replace('_', ' ')
    library_list = []
    variants_maps = {}

    if not trait.replace('_', ' ') in MY_TRAIT_LIST:
        err = 'trait not found'

    else:
        with pymongo.Connection(port=settings.MONGO_PORT) as connection:
            db = connection['pergenie']
            data_info = db['data_info']

            uploadeds = list(data_info.find({'user_id': user_id}))
            file_names = [uploaded['name'] for uploaded in uploadeds]

            variants_maps = {}
            for file_name in file_names:
                library_map, variants_maps[file_name] = search_variants.search_variants(user_id, file_name, query, 'trait')

            # pprint(library_map)
            # print variants_maps

            library_list = [library_map[found_id] for found_id in library_map]  ###

    log.error(err)

    return direct_to_template(request,
                              'library_trait.html',
                              {'err': err,
                               'trait_name': query,
                               'library_list': library_list,
                               'variants_maps': variants_maps})


# TODO: table view for snps
@login_required
def snps_index(request):
    err = ''

    catalog_summary = pickle_load_obj(os.path.join(settings.CATALOG_SUMMARY_CACHE_DIR, 'catalog_summary.p'))
    uniq_snps_list = list(catalog_summary['snps'])

    return direct_to_template(request,
                              'library_snps_index.html',
                              {'err': err,
                               'uniq_snps_list': uniq_snps_list
                               })


@login_required
def snps(request, rs):
    """
    /library/snps/rs(\d+)
    """
    try:
        rs = int(rs)
    except ValueError:
        # 404
        pass

    user_id = request.user.username
    err = ''

    with pymongo.Connection(port=settings.MONGO_PORT) as connection:
        db = connection['pergenie']
        data_info = db['data_info']
        uploadeds = list(data_info.find({'user_id': user_id}))
        file_names = [uploaded['name'] for uploaded in uploadeds]

        # data from uploaded files
        variants = {}
        for file_name in file_names:
            variant = db['variants'][user_id][file_name].find_one({'rs': rs})
            variants[file_name] = variant['genotype'] if variant else 'NA'

        # data from dbsnp
        dbsnp = connection['dbsnp']['B132']
        dbsnp_record = dbsnp.find_one({'rs': rs})
        log.debug('dbsnp_record {}'.format(dbsnp_record))

        # TODO: data from HapMap
        # * allele freq by polulation (with allele strand dbsnp oriented)
        # * LD data(r^2)

    # data from gwascatalog
    catalog_records = list(search_catalog.search_catalog_by_query('rs{}'.format(rs)))
    if len(catalog_records) > 0:
        catalog_record = catalog_records[0]
        if catalog_record['risk_allele_frequency']:
            catalog_record.update({'allele1': catalog_record['risk_allele'],
                                   'allele1_freq': catalog_record['risk_allele_frequency']*100,
                                   'allele2': 'other',
                                   'allele2_freq': (1 - catalog_record['risk_allele_frequency'])*100})
        else:
            err = 'allele frequency is not available...'
            catalog_record.update({'allele1': catalog_record['risk_allele'],
                                   'allele1_freq': None,
                                   'allele2': 'other',
                                   'allele2_freq': None})
    else:
        catalog_record = None

    return direct_to_template(request,
                              'library_snps.html',
                              {'err': err,
                               'rs': rs,
                               'dbsnp_record': dbsnp_record,
                               'catalog_record': catalog_record,
                               'variants': variants})
