# -*- coding: utf-8 -*- 

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.generic.simple import direct_to_template

import pymongo
from lib.mongo import search_variants
from lib.mongo import search_catalog

#
from lib.mongo import my_trait_list
MY_TRAIT_LIST = my_trait_list.my_trait_list
MY_TRAIT_LIST_JA = my_trait_list.my_trait_list_ja

#
from apps.library.forms import LibraryForm

# @require_http_methods(['GET', 'POST'])
@login_required
# def index(response):
def index(request):
    user_id = request.user.username
    err = ''

    # if request.method == 'POST':
    #     # if query:
    #     with pymongo.Connection() as connection:
    #         db = connection['pergenie']
    #         data_info = db['data_info']

    #         uploadeds = list(data_info.find( {'user_id': user_id} ))
    #         file_name = uploadeds[0]['name']

    #         query = '"{}"'.format(CatalogForm.query)
    #         catalog_map, variants_map = search_variants.search_variants(user_id, file_name, query)
    #         catalog_list = [catalog_map[found_id] for found_id in catalog_map] ### somehow catalog_map.found_id does not work in templete...
            
    #         return direct_to_template(request,
    #                                   'catalog_trait.html',
    #                                   {'err': err,
    #                                    'trait_name': query,
    #                                    'catalog_list': catalog_list,
    #                                    'variants_map': variants_map})


    my_trait_list_underbar = [trait.replace(' ', '_') for trait in MY_TRAIT_LIST]  ### TODO: use formatting function
    my_trait_list_ja_underbar = [trait.replace(' ', '_') for trait in MY_TRAIT_LIST_JA]  ### TODO: use formatting function

    return direct_to_template(request,
                              'library.html',
                              {'err': err,
                               'my_trait_list': MY_TRAIT_LIST,
                               'my_trait_list_underbar': my_trait_list_underbar,
                               'my_trait_list_ja_underbar': my_trait_list_ja_underbar,
                               })


@login_required
def trait(request, trait):
    user_id = request.user.username
    err = ''

    if not trait.replace('_', ' ') in MY_TRAIT_LIST:
        err = 'trait not found'
        print 'err', err
        
        my_trait_list_underbar = [trait.replace(' ', '_') for trait in MY_TRAIT_LIST]  ###
        return direct_to_template(request,
                                  'library.html',
                                  {'err': err,
                                   'my_trait_list': MY_TRAIT_LIST,
                                   'my_trait_list_underbar': my_trait_list_underbar})


    with pymongo.Connection() as connection:
        db = connection['pergenie']
        data_info = db['data_info']

        uploadeds = list(data_info.find( {'user_id': user_id}))
        file_names = [uploaded['name'] for uploaded in uploadeds]

        query = '"{}"'.format(trait.replace('_', ' '))
        variants_maps = {}
        for file_name in file_names:
            library_map, variants_maps[file_name] = search_variants.search_variants(user_id, file_name, query)
        library_list = [library_map[found_id] for found_id in library_map] ###

        return direct_to_template(request,
                                  'library_trait.html',
                                  {'err': err,
                                   'trait_name': query,
                                   'library_list': library_list,
                                   'variants_maps': variants_maps})

    # return direct_to_template(response, 'library_trait.html')


# TODO: table view for snps
# @login_required
# def snps_table(request, rs):


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

    with pymongo.Connection() as connection:
        db = connection['pergenie']
        data_info = db['data_info']
        uploadeds = list(data_info.find( {'user_id': user_id}))
        file_names = [uploaded['name'] for uploaded in uploadeds]

        # data from uploaded files
        variants = {}
        for file_name in file_names:
            variant = db['variants'][user_id][file_name].find_one({'rs': rs})
            variants[file_name] = variant['genotype'] if variant else 'NA'

        # data from dbsnp
        dbsnp = connection['dbsnp']['B132']
        dbsnp_record = dbsnp.find_one({'rs': rs})
        print 'dbsnp_record', dbsnp_record

    # data from gwascatalog
    catalog_records = list(search_catalog.search_catalog_by_query('rs{}'.format(rs)))
    if len(catalog_records) > 0:
        catalog_record = catalog_records[0]
        if catalog_record['risk_allele_frequency']:
            catalog_record.update({'allele1': catalog_record['risk_allele'],
                           'allele1_freq': catalog_record['risk_allele_frequency']*100,
                           'allele2': 'other',
                           'allele2_freq': (1 - catalog_record['risk_allele_frequency'])*100
                           })
        else:
            err = 'allele frequency is not available...'
            catalog_record.update({'allele1': catalog_record['risk_allele'],
                           'allele1_freq': None,
                           'allele2': 'other',
                           'allele2_freq': None
                           })
    else:
        catalog_record = None

    # TODO: data from HapMap
    # * allele freq, genotype freq
    # * LD data(r^2)

    return direct_to_template(request,
                              'library_snps.html',
                              {'err': err,
                               'rs': rs,
                               'dbsnp_record': dbsnp_record,
                               'catalog_record': catalog_record,
                               'variants': variants})
