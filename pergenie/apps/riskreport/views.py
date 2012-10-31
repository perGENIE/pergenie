# -*- coding: utf-8 -*- 

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.generic.simple import direct_to_template

import datetime
import os
import pymongo
import mongo.search_variants as search_variants
import mongo.risk_report as risk_report

from apps.riskreport.forms import RiskReportForm

UPLOAD_DIR = '/tmp/pergenie'

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
            tmp_infos = []

            if not infos:
                err = 'no data uploaded'
                break
            print infos

            if request.method == 'POST':
                form = RiskReportForm(request.POST)
                if not form.is_valid():
                    err = 'Invalid request'
                    break

                file_names = []
                file_names.append(request.POST['file_name'])
                file_names.append(request.POST['file_name2'])
                for i, file_name in enumerate(file_names):
                    print 'file_name{0} from form: {1}'.format(i+1, file_name)

                    for info in infos:
                        print info['name'], bool(info['name'] == file_name)
                        if info['name'] == file_name:
                            tmp_info = info
                            tmp_infos.append(tmp_info)
                            break

                    if not tmp_info:
                        err = '{} does not exist'.format(file_name)
                        break

            else:
                tmp_infos.append(infos[0])
            print '[INFO] tmp_infos', tmp_infos


            # TODO: couple veiw (show two genomes at once)
            risk_values = []
            for i, tmp_info in enumerate(tmp_infos):
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
                                                                        tmp_info['sex'], tmp_info['user_id'], tmp_info['name'], 
                                                                        False, True,
                                                                        os.path.join(UPLOAD_DIR, user_id, '{}_{}.p'.format(tmp_info['user_id'], tmp_info['name'])))

                # list for chart
                if i == 0:
                    risk_traits = [k for k,v in sorted(risk_reports.items(), key=lambda(k,v):(v,k), reverse=True)]

                # TODO: min & max
                tmp_trait_value_map = {}

                for (trait,studies) in risk_reports.items():
                    for j, (study, value) in enumerate(sorted(studies.items(), key=lambda(study,value):(value,study), reverse=True)):
                        if j == 0:
                            tmp_trait_value_map[trait] = value

                
                if i == 0:
                    values_to_chart = [v for k,v in sorted(tmp_trait_value_map.items(), key=lambda(k,v):(v,k), reverse=True)]
                    risk_values.append(values_to_chart)

                elif i == 1:
                    risk_values.append([tmp_trait_value_map.get(risk_trait, 1.0) for risk_trait in risk_traits])

            break

        return direct_to_template(request,
                                  'risk_report.html',
                                  {'msg': msg,
                                   'err': err,
                                   'infos': infos,
                                   'tmp_infos': tmp_infos,
                                   'risk_reports': risk_reports,
                                   'risk_traits': risk_traits,
                                   'risk_values': risk_values})


@login_required
def trait(request, file_name, trait):
    """
    view for each trait, show risk value by studies
    """

    user_id = request.user.username
    msg = ''
    err = ''
    tmp_risk_store = None
    tmp_risk_value = None

    print '[DEBUG]trait', trait

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

            print infos
            print 'file_name', file_name
            for info in infos:
                print info['name'], bool(info['name'] == file_name)
                if info['name'] == file_name:
                    tmp_info = info
                    break

            if not tmp_info:
                err = '{} does not exist'.format(file_name)
                break

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
                                                                    tmp_info['sex'], tmp_info['user_id'], tmp_info['name'],
                                                                    False,
                                                                    os.path.join(UPLOAD_DIR, user_id, '{}_{}.p'.format(tmp_info['user_id'], tmp_info['name'])))

            tmp_study_value_map = risk_reports.get(trait)
            tmp_risk_store = risk_store.get(trait)

            # list for chart
            study_list = [k for k,v in sorted(tmp_study_value_map.items(), key=lambda(k,v):(v,k), reverse=True)]
            RR_list = [v for k,v in sorted(tmp_study_value_map.items(), key=lambda(k,v):(v,k), reverse=True)]

            print '[DEBUG] study_list', study_list
            print '[DEBUG] RR_list', RR_list

            break


#         if not trait.replace('_', ' ') in tmp_risk_store:
#             err = 'trait not found'
#             print 'err', err           


        return direct_to_template(request,
                                  'risk_report_trait.html',
                                  {'msg': msg,
                                   'err': err,
                                   'trait_name': trait,
                                   'file_name': file_name,
                                   'infos': infos,
                                   'tmp_info': tmp_info,
                                   'tmp_risk_value': tmp_risk_value,
                                   'tmp_risk_store': tmp_risk_store,
                                   'study_list': study_list,
                                   'RR_list': RR_list
                                   })



@login_required
def study(request, file_name, trait, study_name):
    """
    view for each study, show RR by rss
    """

    user_id = request.user.username
    msg = ''
    err = ''
    tmp_risk_store = None
    tmp_risk_value = None

    with pymongo.Connection() as connection:
        db = connection['pergenie']
        data_info = db['data_info']

        while True:
            print '[DEBUG] in view for study'
            # determine file
            infos = list(data_info.find( {'user_id': user_id} ))
            tmp_info = None

            if not infos:
                err = 'no data uploaded'
                break

            print infos
            print 'file_name', file_name
            for info in infos:
                print info['name'], bool(info['name'] == file_name)
                if info['name'] == file_name:
                    tmp_info = info
                    break

            if not tmp_info:
                err = '{} does not exist'.format(file_name)
                break

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
                                                                    tmp_info['sex'], tmp_info['user_id'], tmp_info['name'],
                                                                    False,
                                                                    os.path.join(UPLOAD_DIR, user_id, '{}_{}.p'.format(tmp_info['user_id'], tmp_info['name'])))
            tmp_risk_store = risk_store.get(trait).get(study_name)

            # list for chart
            snps_list = [k for k,v in sorted(tmp_risk_store.items(), key=lambda x:x[1]['RR'])]
            RR_list = [v['RR'] for k,v in sorted(tmp_risk_store.items(), key=lambda x:x[1]['RR'])]

            break


        if not trait.replace('_', ' ') in risk_store:
            err = 'trait not found'
            print 'err', err           


        return direct_to_template(request,
                                  'risk_report_study.html',
                                  {'msg': msg,
                                   'err': err,
                                   'trait_name': trait,
                                   'file_name': file_name,
                                   'infos': infos,
                                   'tmp_info': tmp_info,
                                   'tmp_risk_store': tmp_risk_store,
                                   'snps_list': snps_list,
                                   'RR_list': RR_list,
                                   'study_name': study_name
                                   })

