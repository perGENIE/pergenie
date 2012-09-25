from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.generic.simple import direct_to_template

import datetime
import os
import pymongo
import mongo.search_variants as search_variants
import mongo.risk_report as risk_report

# @require_http_methods(['GET', 'POST'])
@login_required
def index(request):
    user_id = request.user.username
    msg = ''
    err = ''

    with pymongo.Connection() as connection:
        db = connection['pergenie']
        data_info = db['data_info']

        while True:
            infos = list(data_info.find( {'user_id': user_id} ))
            print infos
            if not infos:
                err = 'no data uploaded'
                break

            # TODO: support multiple data.
            info = infos[0]  # temporary choose first one
            

            # TODO: population mapping
            # ------------------------
            population_map = {'Asian': ['African'],
                              'Europian': ['European', 'Caucasian'],
                              'African': ['Chinese', 'Japanese', 'Asian'],
                              'Japanese': ['Japanese', 'Asian'],
                              'none': ['']}
            population = 'population:{}'.format('+'.join(population_map[info['population']]))

            catalog_map, variants_map = search_variants.search_variants(info['user_id'], info['name'], population)

            population_code_map = {'Asian': 'JPT',
                                   'Europian': 'CEU',
                                   'Japanese': 'JPT',
                                   'none': 'CEU'}
            print info['population'], population_code_map[info['population']]

            risk_store, risk_reports = risk_report.risk_calculation(catalog_map, variants_map, population_code_map[info['population']], is_LD_block_clustered=False)


            break

        print risk_reports
        risk_traits = [k.encode('euc_jp') for k,v in risk_reports.items()]
        print risk_traits
        risk_values = [round(v, 3) for k,v in risk_reports.items()]


        return direct_to_template(request,
                                  'risk_report.html',
                                  {'msg': msg,
                                   'err': err,
                                   'risk_reports': risk_reports,
                                   'risk_traits': risk_values,
                                   'risk_values': risk_values})
