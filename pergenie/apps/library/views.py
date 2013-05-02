# -*- coding: utf-8 -*-
import os

from django.contrib.auth.decorators import login_required
# from django.views.decorators.http import require_http_methods
from django.views.generic.simple import direct_to_template
from django.utils import translation
from django.utils.translation import ugettext as _
from django.conf import settings
# from apps.library.forms import LibraryForm

import pymongo

from lib.mongo import search_variants
from lib.mongo import search_catalog
from lib.mongo.get_latest_catalog import get_latest_catalog
from lib.mongo.get_traits_infos import get_traits_infos
from lib.utils.io import pickle_load_obj
from lib.utils.clogging import getColorLogger
log = getColorLogger(__name__)

TRAITS, TRAITS_JA, TRAITS_CATEGORY, TRAITS_WIKI_URL_EN = get_traits_infos()

@login_required
def index(request):
    msg, err = '', ''

    with pymongo.Connection(port=settings.MONGO_PORT) as connection:
        catalog_info = connection['pergenie']['catalog_info']
        latest_catalog_date = catalog_info.find_one({'status': 'latest'})['date']

    return direct_to_template(request, 'index.html',
                              dict(user_id=request.user.username, msg=msg, err=err,
                                   dbsnp_version=settings.DBSNP_VERSION, refgenome_version=settings.REFGENOME_VERSION,
                                   latest_catalog_date=latest_catalog_date))


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

    return direct_to_template(request, 'library/summary_index.html',
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
    msg, err = '', ''
    is_ja = bool(translation.get_language() == 'ja')

    return direct_to_template(request, 'library/trait_index.html',
                              dict(user_id=request.user.username, msg=msg, err=err,
                                   is_ja=is_ja,
                                   traits=TRAITS, traits_ja=TRAITS_JA, traits_category=TRAITS_CATEGORY,
                                   wiki_url_en=TRAITS_WIKI_URL_EN))


@login_required
def trait(request, trait):
    user_id = request.user.username
    msg, err = '', ''

    library_list = []
    variants_maps = {}

    if not trait in TRAITS:
        err += 'trait not found'

    else:
        # get variants data
        with pymongo.Connection(port=settings.MONGO_PORT) as connection:

            # for debug
            catalog = get_latest_catalog()
            founds = catalog.find({'trait': trait})
            log.debug('catalog.find: {}'.format(list(founds)))

            data_info = connection['pergenie']['data_info']

            uploadeds = list(data_info.find({'user_id': user_id}))
            file_names = [uploaded['name'] for uploaded in uploadeds]

            variants_maps = {}
            for file_name in file_names:
                library_map, variants_maps[file_name] = search_variants.search_variants(user_id, file_name, trait, 'trait')

            library_list = [library_map[found_id] for found_id in library_map]  ###
            log.debug(library_list)

    log.error(err)

    return direct_to_template(request, 'library/trait.html',
                              dict(user_id=request.user.username, msg=msg, err=err,
                                   trait_name=trait, library_list=library_list,
                                   variants_maps=variants_maps))


# TODO: table view for snps
@login_required
def snps_index(request):
    err = ''

    catalog_summary = pickle_load_obj(os.path.join(settings.CATALOG_SUMMARY_CACHE_DIR, 'catalog_summary.p'))
    uniq_snps_list = list(catalog_summary['snps'])

    return direct_to_template(request,
                              'library/snps_index.html',
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
                              'library/snps.html',
                              {'err': err,
                               'rs': rs,
                               'dbsnp_record': dbsnp_record,
                               'catalog_record': catalog_record,
                               'variants': variants})
