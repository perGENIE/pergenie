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
            
            # TODO: population
            catalog_map, variants_map = search_variants.search_variants(info['user_id'], info['name'],
                                                                        'population:{}'.format(''))
            risk_store, risk_reports = risk_report.risk_calculation(catalog_map, variants_map)

            # for (trait,risk_value) in sorted(risk_reports.items(), key=lambda(k,v):(v,k), reverse=True):            
            break

        return direct_to_template(request,
                                  'risk_report.html',
                                  {'msg': msg, 'err': err, 'risk_reports': risk_reports})
