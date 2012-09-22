from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.generic.simple import direct_to_template

import pymongo
from lib.mongo import search_variants

from lib.mongo import my_trait_list
MY_TRAIT_LIST = my_trait_list.my_trait_list
MY_TRAIT_LIST_JA = my_trait_list.my_trait_list_ja

#
from apps.catalog.forms import CatalogForm

@require_http_methods(['GET', 'POST'])
@login_required
# def index(response):
def index(request):
    user_id = request.user.username
    err = ''

    if request.method == 'POST':
        # if query:
        with pymongo.Connection() as connection:
            db = connection['pergenie']
            data_info = db['data_info']

            uploadeds = list(data_info.find( {'user_id': user_id} ))
            file_name = uploadeds[0]['name']

            query = '"{}"'.format(CatalogForm.query)
            catalog_map, variants_map = search_variants.search_variants(user_id, file_name, query)
            catalog_list = [catalog_map[found_id] for found_id in catalog_map] ### somehow catalog_map.found_id does not work in templete...
            
            return direct_to_template(request,
                                      'catalog_records.html',
                                      {'err': err,
                                       'trait_name': query,
                                       'catalog_list': catalog_list,
                                       'variants_map': variants_map})


    my_trait_list_underbar = [trait.replace(' ', '_') for trait in MY_TRAIT_LIST]  ### TODO: use formatting function
    my_trait_list_ja_underbar = [trait.replace(' ', '_') for trait in MY_TRAIT_LIST_JA]  ### TODO: use formatting function

    return direct_to_template(request,
                              'catalog.html',
                              {'err': err,
                               'my_trait_list': MY_TRAIT_LIST,
                               'my_trait_list_underbar': my_trait_list_underbar,
                               'my_trait_list_ja_underbar': my_trait_list_ja_underbar,
                               })


@login_required
def catalog(request, trait):
    user_id = request.user.username
    err = ''

    print 'trait', trait
    
    if not trait.replace('_', ' ') in MY_TRAIT_LIST:
        err = 'trait not found'
        print 'err', err
        
        my_trait_list_underbar = [trait.replace(' ', '_') for trait in MY_TRAIT_LIST]  ###
        return direct_to_template(request,
                                  'catalog.html',
                                  {'err': err,
                                   'my_trait_list': MY_TRAIT_LIST,
                                   'my_trait_list_underbar': my_trait_list_underbar})


    with pymongo.Connection() as connection:
        db = connection['pergenie']
        data_info = db['data_info']

        uploadeds = list(data_info.find( {'user_id': user_id} ))
        file_name = uploadeds[0]['name']

        query = '"{}"'.format(trait.replace('_', ' '))
        catalog_map, variants_map = search_variants.search_variants(user_id, file_name, query)
        catalog_list = [catalog_map[found_id] for found_id in catalog_map] ###

        return direct_to_template(request,
                                  'catalog_records.html',
                                  {'err': err,
                                   'trait_name': query,
                                   'catalog_list': catalog_list,
                                   'variants_map': variants_map})

    # return direct_to_template(response, 'catalog_records.html')
