# -*- coding: utf-8 -*-
import sys, os
from pymongo import MongoClient

from django.utils.translation import get_language
from django.conf import settings

from lib.mongo.get_latest_catalog import get_latest_catalog
from lib.mongo.get_traits_infos import get_traits_infos
from lib.mongo.reliability_rank import calc_reliability_rank, get_highest_priority_study
import lib.mongo.search_variants as search_variants
import lib.mongo.risk_report as risk_report
from utils.io import pickle_dump_obj, pickle_load_obj
from utils.date import today_date, today_str
from utils import clogging
log = clogging.getColorLogger(__name__)

TRAITS, TRAITS2JA, TRAITS2CATEGORY, TRAITS2WIKI_URL_EN = get_traits_infos(as_dict=True)
JA2TRAITS = dict([(v, k) for (k, v) in TRAITS2JA.items()])


def get_user_infos(user_id):
    with MongoClient(port=settings.MONGO_PORT) as c:
        data_info = c['pergenie']['data_info']
        infos = list(data_info.find({'user_id': user_id}))

        return infos


def upsert_riskreport(tmp_info, mongo_port=settings.MONGO_PORT):
    # TODO: replace pickle to mongo
    """Upsert risk report for <file_name> of <user>.
    """

    # calculate risk
    population = 'population:{}'.format('+'.join(settings.POPULATION_MAP[tmp_info['population']]))
    catalog_map, variants_map = search_variants.search_variants(tmp_info['user_id'], tmp_info['name'], population)

    risk_store, risk_reports = risk_report.risk_calculation(catalog_map, variants_map, settings.POPULATION_CODE_MAP[tmp_info['population']],
                                                            tmp_info['sex'], tmp_info['user_id'], tmp_info['name'], False, True)

    # set reliability rank
    tmp_risk_reports = dict()
    for trait,studies in risk_reports.items():
        tmp_risk_reports[trait] = {}

        for study,value in studies.items():
            record = risk_store[trait][study].values()[0]['catalog_map']
            r_rank = calc_reliability_rank(record)
            tmp_risk_reports[trait].update({study: [r_rank, value]})
    risk_reports = tmp_risk_reports

    # dump as pickle
    pickle_dump_obj(risk_store, os.path.join(settings.RISKREPORT_CACHE_DIR, tmp_info['user_id'], 'risk_store.{0}.{1}.p'.format(tmp_info['user_id'], tmp_info['name'])))
    pickle_dump_obj(risk_reports, os.path.join(settings.RISKREPORT_CACHE_DIR, tmp_info['user_id'], 'risk_reports.{0}.{1}.p'.format(tmp_info['user_id'], tmp_info['name'])))

    # upsert data_info['riskreport'] = today
    with MongoClient(port=settings.MONGO_PORT) as c:
        data_info = c['pergenie']['data_info']
        data_info.update({'user_id': tmp_info['user_id'], 'name': tmp_info['name'] }, {"$set": {'riskreport': today_date}}, upsert=True)


def get_risk_values_for_indexpage(tmp_infos, category=[], is_higher=False, is_lower=False, top=None, is_log=True):
    """Return risk values (for one or two files) for chart.
    """

    with MongoClient(port=settings.MONGO_PORT) as c:
        data_info = c['pergenie']['data_info']

        for i, tmp_info in enumerate(tmp_infos):
            # check if riskreport.<user>.<file_name> exist and latest in data_info
            tmp_data_info = data_info.find_one({'user_id': tmp_info['user_id'],
                                                'name': tmp_info['name']})
            risk_report_date = tmp_data_info.get('riskreport', None)
            risk_report_obj = os.path.join(settings.RISKREPORT_CACHE_DIR,
                                           tmp_info['user_id'],
                                           'risk_reports.{0}.{1}.p'.format(tmp_info['user_id'], tmp_info['name']))

            # # check date
            # if not os.path.exists(risk_report_obj) or (today_date > risk_report_date):
            #     upsert_riskreport(tmp_info)

            # or always upsert
            upsert_riskreport(tmp_info)

            # load latest risk_store.p & risk_report.p

            log.debug('load pickle:' + os.path.join(settings.RISKREPORT_CACHE_DIR, tmp_info['user_id'], 'risk_store.{0}.{1}.p'.format(tmp_info['user_id'], tmp_info['name'])))
            risk_store = pickle_load_obj(os.path.join(settings.RISKREPORT_CACHE_DIR, tmp_info['user_id'], 'risk_store.{0}.{1}.p'.format(tmp_info['user_id'], tmp_info['name'])))
            risk_reports = pickle_load_obj(os.path.join(settings.RISKREPORT_CACHE_DIR, tmp_info['user_id'], 'risk_reports.{0}.{1}.p'.format(tmp_info['user_id'], tmp_info['name'])))

            # create list for chart
            tmp_map = {}
            for trait,studies in risk_reports.items():
                if TRAITS2CATEGORY.get(trait) in category:

                    highest = get_highest_priority_study(studies)
                    tmp_map[trait] = [highest['value'],
                                      highest['rank'],
                                      highest['study']]

            # values of first user
            if i == 0:

                # filter for is_higher & is_lower as is_ok
                if is_higher:
                    is_ok = lambda x: x >= 0.0
                elif is_lower:
                    is_ok = lambda x: x <= 0.0
                else:
                    is_ok = lambda x: True

                # filter for is_log (default return value of risk_report() is in log)
                if is_log:
                    to_log = lambda x: x
                elif not is_log:
                    to_log = lambda x: 10**x

                if not top: top = 2000  ###
                risk_traits = [k for k,v in sorted(tmp_map.items(), key=lambda(k,v):(v,k), reverse=True) if is_ok(v[0])][:int(top)]
                risk_values = [[round(to_log(v[0]), 1) for k,v in sorted(tmp_map.items(), key=lambda(k,v):(v,k), reverse=True) if is_ok(v[0])][:int(top)]]
                risk_ranks = [v[1] for k,v in sorted(tmp_map.items(), key=lambda(k,v):(v,k), reverse=True) if is_ok(v[0])][:int(top)]
                risk_studies = [v[2] for k,v in sorted(tmp_map.items(), key=lambda(k,v):(v,k), reverse=True) if is_ok(v[0])][:int(top)]

            # values of second user
            elif i >= 1:
                risk_values.append([tmp_map.get(trait, 0) for trait in risk_traits])
                # TODO:

    return risk_reports, risk_traits, risk_values, risk_ranks, risk_studies


def get_risk_infos_for_subpage(user_id, file_name, trait_name=None, study_name=None):
    msg, err = '', ''
    infos, tmp_info, tmp_risk_store  = None, None, None
    RR_list, RR_list_real, study_list, snps_list = [], [], [], []
    browser_language = get_language()

    with MongoClient(port=settings.MONGO_PORT) as c:
        data_info = c['pergenie']['data_info']

        while True:
            # reverse translation (to English)
            trait_name = JA2TRAITS.get(trait_name, trait_name)

            if not trait_name in TRAITS:
                err = _('trait not found')
                break

            # determine file
            tmp_data_info = data_info.find_one({'user_id': user_id, 'name': file_name})

            if not tmp_data_info:
                err = _('no such file %(file_name)s') % {'file_name': file_name}
                break

            # check if riskreport.<user>.<file_name> exist and latest in data_info
            risk_report_date = tmp_data_info.get('riskreport', None)

            risk_report_obj = os.path.join(settings.RISKREPORT_CACHE_DIR, user_id, 'risk_reports.{0}.{1}.p'.format(user_id, file_name))
            if not os.path.exists(risk_report_obj) or (today_date > risk_report_date):
                upsert_riskreport(tmp_info)

            # load latest risk_store.p & risk_report.p
            risk_store = pickle_load_obj(os.path.join(settings.RISKREPORT_CACHE_DIR, user_id, 'risk_store.{0}.{1}.p'.format(user_id, file_name)))
            risk_reports = pickle_load_obj(os.path.join(settings.RISKREPORT_CACHE_DIR, user_id, 'risk_reports.{0}.{1}.p'.format(user_id, file_name)))

            if study_name and trait_name:
                tmp_risk_store = risk_store.get(trait_name).get(study_name)

                snps_list = [k for k,v in sorted(tmp_risk_store.items(), key=lambda x:x[1]['RR'])]
                RR_list = [v['RR'] for k,v in sorted(tmp_risk_store.items(), key=lambda x:x[1]['RR'])]
                reliability_list = [risk_reports.get(trait_name).get(study_name)[0]]


            elif not study_name and trait_name:
                # Studies for a trait
                tmp_risk_store = risk_store.get(trait_name)
                tmp_study_value_map = risk_reports.get(trait_name)
                print '###'
                print risk_reports
                print
                study_list = [k for k,v in sorted(tmp_study_value_map.items(), key=lambda(k,v):(v,k), reverse=True)]

                # list for chart
                RR_list = [v[1] for k,v in sorted(tmp_study_value_map.items(), key=lambda(k,v):(v,k), reverse=True)]
                RR_list_real = [round(10**v[1], 3) for k,v in sorted(tmp_study_value_map.items(), key=lambda(k,v):(v,k), reverse=True)]
                reliability_list = [v[0] for k,v in sorted(tmp_study_value_map.items(), key=lambda(k,v):(v,k), reverse=True)]

            else:
                pass

            # translation to Japanese
            if browser_language == 'ja':
                log.debug('trans')
                trait_name_ja = TRAITS2JA.get(trait_name)
                trait_name = trait_name_ja
                log.debug(trait_name)

            break

        return dict(msg=msg, err=err, infos=infos, tmp_info=tmp_info,
                    RR_list=RR_list, RR_list_real=RR_list_real,
                    study_list=study_list, reliability_list=reliability_list,
                    file_name=file_name, trait_name=trait_name, study_name=study_name,
                    snps_list=snps_list, tmp_risk_store=tmp_risk_store)
