# -*- coding: utf-8 -*- 

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.generic.simple import direct_to_template

import datetime
import os
import pymongo
import mongo.search_variants as search_variants
import mongo.risk_report as risk_report
import numpy as np


from pprint import pprint
import colors

from apps.riskreport.forms import RiskReportForm

UPLOAD_DIR = '/tmp/pergenie'

POPULATION_MAP = {'Asian': ['African'],
                  'Europian': ['European', 'Caucasian'],
                  'African': ['Chinese', 'Japanese', 'Asian'],
                  'Japanese': ['Japanese', 'Asian'],
                  'unkown': ['']}

POPULATION_CODE_MAP = {'Asian': 'JPT',
                       'Europian': 'CEU',
                       'Japanese': 'JPT',
                       'unkown': 'unkown'}

def get_risk_values(tmp_infos):
    for i, tmp_info in enumerate(tmp_infos):
        # calculate risk
        population = 'population:{}'.format('+'.join(POPULATION_MAP[tmp_info['population']]))
        catalog_map, variants_map = search_variants.search_variants(tmp_info['user_id'], tmp_info['name'], population)
        risk_store, risk_reports = risk_report.risk_calculation(catalog_map, variants_map, POPULATION_CODE_MAP[tmp_info['population']],
                                                                tmp_info['sex'], tmp_info['user_id'], tmp_info['name'], 
                                                                False,  True, None)
                                                                # os.path.join(UPLOAD_DIR, user_id, '{}_{}.p'.format(tmp_info['user_id'], tmp_info['name'])))

        # list for chart
        tmp_map = {}
        for trait,studies in risk_reports.items():
            tmp_map[trait] = np.mean(studies.values())

        if i == 0:
            risk_traits = [k for k,v in sorted(tmp_map.items(), key=lambda(k,v):(v,k), reverse=True)]
            risk_values = [[v for k,v in sorted(tmp_map.items(), key=lambda(k,v):(v,k), reverse=True)]]

        elif i >= 1:
            risk_values.append([tmp_map.get(trait, 0) for trait in risk_traits])
            
    return risk_reports, risk_traits, risk_values


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

                file_names = [request.POST['file_name'], request.POST['file_name2']]
                for i, file_name in enumerate(file_names):
                    print 'file_name{0} from form: {1}'.format(i+1, file_name)

                    for info in infos:
                        print info['name'], bool(info['name'] == file_name)
                        if info['name'] == file_name:
                            tmp_info = info
                            tmp_infos.append(tmp_info)
                            break

                    # TODO: if file is in importing, break

                    if not tmp_info:
                        err = '{} does not exist'.format(file_name)
                        break

            else:
                tmp_infos.append(infos[0])
            print '[INFO] tmp_infos', tmp_infos

            risk_reports, risk_traits, risk_values = get_risk_values(tmp_infos)
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

            print 'tmp_info', tmp_info

            # calculate risk
            population = 'population:{}'.format('+'.join(POPULATION_MAP[tmp_info['population']]))
            catalog_map, variants_map = search_variants.search_variants(tmp_info['user_id'], tmp_info['name'], population)
            risk_store, risk_reports = risk_report.risk_calculation(catalog_map, variants_map, POPULATION_CODE_MAP[tmp_info['population']],
                                                                    tmp_info['sex'], tmp_info['user_id'], tmp_info['name'],
                                                                    False, True, None)
                                                                    # os.path.join(UPLOAD_DIR, user_id, '{}_{}.p'.format(tmp_info['user_id'], tmp_info['name'])))

            tmp_study_value_map = risk_reports.get(trait)
            tmp_risk_store = risk_store.get(trait)

            # list for chart
            if tmp_study_value_map:
                study_list = [k for k,v in sorted(tmp_study_value_map.items(), key=lambda(k,v):(v,k), reverse=True)]
                RR_list = [v for k,v in sorted(tmp_study_value_map.items(), key=lambda(k,v):(v,k), reverse=True)]
            else:
                err = '{0} is not available for {1}'.format()


            break

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

            # calculate risk
            population = 'population:{}'.format('+'.join(POPULATION_MAP[tmp_info['population']]))

            catalog_map, variants_map = search_variants.search_variants(tmp_info['user_id'], tmp_info['name'], population)

            risk_store, risk_reports = risk_report.risk_calculation(catalog_map, variants_map, POPULATION_CODE_MAP[tmp_info['population']],
                                                                    tmp_info['sex'], tmp_info['user_id'], tmp_info['name'],
                                                                    False, True, None) #                                                                     os.path.join(UPLOAD_DIR, user_id, '{}_{}.p'.format(tmp_info['user_id'], tmp_info['name'])))
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

