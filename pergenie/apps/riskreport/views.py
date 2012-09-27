from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.generic.simple import direct_to_template

import datetime
import os
import pymongo
import mongo.search_variants as search_variants
import mongo.risk_report as risk_report

from apps.riskreport.forms import RiskReportForm

@require_http_methods(['GET', 'POST'])
@login_required
def index(request):
    user_id = request.user.username
    msg = ''
    err = ''
    risk_reports = None
    risk_values = None

    with pymongo.Connection() as connection:
        db = connection['pergenie']
        data_info = db['data_info']

        while True:
            # determine file
            infos = list(data_info.find( {'user_id': user_id} ))
            tmp_info = None

            if not infos:
                err = 'no data uploaded'
                break

            if request.method == 'POST':
                form = RiskReportForm(request.POST)
                if not form.is_valid():
                    err = 'Invalid request'
                    break
                file_name = request.POST['file_name']
                print 'file_name from form:', file_name

                print infos
                for info in infos:
                    print info['name'], bool(info['name'] == file_name)
                    if info['name'] == file_name:
                        tmp_info = info
                        break

                if not tmp_info:
                    err = '{} does not exist'.format(file_name)
                    break

            else:
                tmp_info = infos[0]
            print 'tmp_info', tmp_info

            # TODO: population mapping
            # ------------------------
            population_map = {'Asian': ['African'],
                              'Europian': ['European', 'Caucasian'],
                              'African': ['Chinese', 'Japanese', 'Asian'],
                              'Japanese': ['Japanese', 'Asian'],
                              'unkown': ['']}
            population = 'population:{}'.format('+'.join(population_map[tmp_info['population']]))

            catalog_map, variants_map = search_variants.search_variants(tmp_info['user_id'], tmp_info['name'], population)

            population_code_map = {'Asian': 'JPT',
                                   'Europian': 'CEU',
                                   'Japanese': 'JPT',
                                   'unkown': 'unkown'}
            print tmp_info['population'], population_code_map[tmp_info['population']]


            risk_store, risk_reports = risk_report.risk_calculation(catalog_map, variants_map, population_code_map[tmp_info['population']],
                                                                    tmp_info['sex'], is_LD_block_clustered=False)

            print risk_reports
            risk_traits = [k.encode('euc_jp') for k,v in risk_reports.items()]
            print risk_traits
            risk_values = [round(v, 3) for k,v in risk_reports.items()]

            break

        return direct_to_template(request,
                                  'risk_report.html',
                                  {'msg': msg,
                                   'err': err,
                                   'infos': infos,
                                   'tmp_info': tmp_info,
                                   'risk_reports': risk_reports,
                                   'risk_traits': risk_values,
                                   'risk_values': risk_values})
