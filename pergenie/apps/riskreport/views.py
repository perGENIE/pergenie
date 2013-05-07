# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.generic.simple import direct_to_template
from django.utils.translation import get_language
from django.utils.translation import ugettext as _
from django.conf import settings

from apps.riskreport.forms import RiskReportForm

import sys
import os
import numpy as np
import re
import pymongo

#
import mongo.search_variants as search_variants
import mongo.risk_report as risk_report

#
from lib.mongo.get_latest_catalog import get_latest_catalog
from lib.mongo.get_traits_infos import get_traits_infos
from utils.io import pickle_dump_obj, pickle_load_obj
from utils.date import today_date, today_str
from utils import clogging
log = clogging.getColorLogger(__name__)

TRAITS, TRAITS2JA, TRAITS2CATEGORY, TRAITS2WIKI_URL_EN = get_traits_infos(as_dict=True)
JA2TRAITS = dict([(v, k) for (k, v) in TRAITS2JA.items()])


def calc_reliability_rank(record):
    """
    >>> record = {'study': 'a', 'p_value': '1e-10'}
    >>> calc_reliability_rank(record)
    '***'
    >>> record = {'study': 'a', 'p_value': '1e-7'}
    >>> calc_reliability_rank(record)
    '**'
    >>> record = {'study': 'a', 'p_value': '1e-4'}
    >>> calc_reliability_rank(record)
    '*'
    >>> record = {'study': 'a', 'p_value': '1e-1'}
    >>> calc_reliability_rank(record)
    ''
    >>> record = {'study': 'a', 'p_value': '0.0'}
    >>> calc_reliability_rank(record)
    ''
    >>> record = {'study': 'Meta-analysis of a', 'p_value': '1e-10'}
    >>> calc_reliability_rank(record)
    'm***'
    >>> record = {'study': 'meta-analysis of a', 'p_value': '1e-10'}
    >>> calc_reliability_rank(record)
    'm***'
    >>> record = {'study': 'meta analysis of a', 'p_value': '1e-10'}
    >>> calc_reliability_rank(record)
    'm***'
    >>> record = {'study': 'a meta analysis of a', 'p_value': '1e-10'}
    >>> calc_reliability_rank(record)
    'm***'
    """

    r_rank = ''

    # is Meta-Analysis of GWAS ?
    if re.search('meta.?analysis', record['study'], re.IGNORECASE):
        r_rank += 'm'

    # p-value based reliability rank:
    #
    #      4   5   6   7   8   9
    # |    |   |   |   |   |   | *
    # | NA |   |   | * | * | * | *
    # |    | * | * | * | * | * | *

    if record['p_value']:
        res = re.findall('(\d+)e-(\d+)', record['p_value'], re.IGNORECASE)

        if not res:
            pass
        else:
            b = float(res[0][1])
            if b < 4:
                pass
            elif 4 <= b < 6:
                r_rank += '*'
            elif 6 <= b < 9:
                r_rank += '**'
            elif 9 <= b:
                r_rank += '***'

    # sample size:
    # TODO: parse sample-size
    # TODO: check the correlation `sample size` and `p-value`
    # if record['initial_sample_size']:

    return r_rank


def get_highest_priority_study(studies):
    """
    >>> data = {'a': ['**', 1.0], 'b': ['*', 1.0]}
    >>> get_highest_priority_study(data)
    {'study': 'a', 'rank': '**', 'value': 1.0}

    >>> data = {'a': ['m**', 1.0], 'b': ['*', 1.0]}
    >>> get_highest_priority_study(data)
    {'study': 'a', 'rank': 'm**', 'value': 1.0}

    >>> data = {'a': ['m**', 1.0], 'b': ['m*', 1.0]}
    >>> get_highest_priority_study(data)
    {'study': 'a', 'rank': 'm**', 'value': 1.0}

    >>> data = {'a': ['**', 1.0], 'b': ['m*', 1.0]}
    >>> get_highest_priority_study(data)
    {'study': 'b', 'rank': 'm*', 'value': 1.0}

    """

    highest = dict(study='', rank='', value=0.0)

    for study,[rank,value] in studies.items():
        record = dict(study=study, rank=rank, value=value)

        if rank.count('*') > highest['rank'].count('*'):
            if ('m' in highest['rank']) and (not 'm' in rank):
                pass
            else:
                highest = record
        elif (not 'm' in highest['rank']) and ('m' in rank):
            highest = record

    return highest


def upsert_riskreport(tmp_info, mongo_port=settings.MONGO_PORT):
    # TODO: replace pickle to mongo
    """Upsert risk report for <file_name> of <user>.
    """

    # calculate risk
    population = 'population:{}'.format('+'.join(settings.POPULATION_MAP[tmp_info['population']]))
    catalog_map, variants_map = search_variants.search_variants(tmp_info['user_id'], tmp_info['name'], population)

    risk_store, risk_reports = risk_report.risk_calculation(catalog_map, variants_map, settings.POPULATION_CODE_MAP[tmp_info['population']],
                                                            tmp_info['sex'], tmp_info['user_id'], tmp_info['name'], False,  True)

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
    with pymongo.Connection(port=settings.MONGO_PORT) as connection:
        data_info = connection['pergenie']['data_info']
        data_info.update({'user_id': tmp_info['user_id'], 'name': tmp_info['name'] }, {"$set": {'riskreport': today_date}}, upsert=True)


def get_risk_values_for_indexpage(tmp_infos, category=[], is_higher=False, is_lower=False, top=None, is_log=True):
    """Return risk values (for one or two files) for chart.
    """

    with pymongo.Connection(port=settings.MONGO_PORT) as connection:
        data_info = connection['pergenie']['data_info']

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


@require_http_methods(['GET', 'POST'])
@login_required
def index(request):
    """
    Summary view for risk report.
    * Show top-10 highest & top-10 lowest risk values.
    * Link to `show all`
    """
    user_id = request.user.username
    msg, err = '', ''
    browser_language = get_language()

    risk_reports, risk_traits, risk_values = None, None, None
    h_risk_reports, h_risk_traits, h_risk_values, h_risk_ranks, h_risk_studies = None, None, None, None, None
    l_risk_reports, l_risk_traits, l_risk_values, l_risk_ranks, l_risk_studies = None, None, None, None, None

    with pymongo.Connection(port=settings.MONGO_PORT) as connection:
        data_info = connection['pergenie']['data_info']

        while True:
            # determine file
            infos = list(data_info.find({'user_id': user_id}))
            tmp_info = None
            tmp_infos = []

            if not infos:
                err = _('no data uploaded')
                break

            if request.method == 'POST':
                form = RiskReportForm(request.POST)
                if not form.is_valid():
                    err = _('Invalid request.')
                    break

                for i, file_name in enumerate([request.POST['file_name']]):
                    for info in infos:
                        if info['name'] == file_name:
                            if not info['status'] == 100:
                                err = _('%(file_name)s is in importing, please wait for seconds...') % {'file_name': file_name}

                            tmp_info = info
                            tmp_infos.append(tmp_info)
                            break

                    if not tmp_info:
                        err = _('no such file %(file_name)s') % {'file_name': file_name}
                        break

            else:
                # choose first file_name by default
                info = infos[0]
                file_name = info['name']
                if not info['status'] == 100:
                    err = _('%(file_name)s is in importing, please wait for seconds...') % {'file_name': file_name}
                tmp_infos.append(info)

            if not err:
                # get top-10 highest & top-10 lowest
                h_risk_reports, h_risk_traits, h_risk_values, h_risk_ranks, h_risk_studies = get_risk_values_for_indexpage(tmp_infos, category=['Disease'], is_higher=True, top=10, is_log=False)
                l_risk_reports, l_risk_traits, l_risk_values, l_risk_ranks, l_risk_studies = get_risk_values_for_indexpage(tmp_infos, category=['Disease'], is_lower=True, top=10, is_log=False)

                # translate to Japanese
                if browser_language == 'ja':
                    h_risk_traits = [TRAITS2JA.get(trait) for trait in h_risk_traits]
                    l_risk_traits = [TRAITS2JA.get(trait) for trait in l_risk_traits]

            break

        return direct_to_template(request, 'risk_report/index.html',
                                  dict(msg=msg, err=err, infos=infos, tmp_infos=tmp_infos,
                                       h_risk_reports=h_risk_reports, h_risk_traits=h_risk_traits, h_risk_values=h_risk_values,
                                       h_risk_ranks=h_risk_ranks, h_risk_studies=h_risk_studies,
                                       l_risk_reports=l_risk_reports, l_risk_traits=l_risk_traits, l_risk_values=l_risk_values,
                                       l_risk_ranks=l_risk_ranks, l_risk_studies=l_risk_studies
                                       ))


@require_http_methods(['GET', 'POST'])
@login_required
def show_all(request):
    """
    Show all risk values in a chart.
    * It can compare two individual genomes.

    TODO:
    * Do not use log-scale. Replace to real-scale.
    * Enable to click & link trait-name in charts. (currently bar in charts only)
    * Show population in charts, e.g., `Japanese national flag`, etc.
    """

    user_id = request.user.username
    msg, err = '', ''
    risk_reports, risk_traits, risk_values = None, None, None
    browser_language = get_language()

    with pymongo.Connection(port=settings.MONGO_PORT) as connection:
        data_info = connection['pergenie']['data_info']

        while True:
            # determine file
            infos = list(data_info.find({'user_id': user_id}))
            tmp_info = None
            tmp_infos = []

            if not infos:
                err = _('no data uploaded')
                break

            if request.method == 'POST':
                """User chose file_name via select box & requested as POST
                """

                log.debug('method == POST')

                form = RiskReportForm(request.POST)
                if not form.is_valid():
                    err = _('Invalid request.')
                    break

                for i, file_name in enumerate([request.POST['file_name'], request.POST['file_name2']]):
                    log.debug('file_name: {0} from form: {1}'.format(i+1, file_name))

                    for info in infos:
                        if info['name'] == file_name:
                            if not info['status'] == 100:
                                # err = str(file_name) + _(' is in importing, please wait for seconds...')
                                err = _('%(file_name)s is in importing, please wait for seconds...') % {'file_name': file_name}

                            tmp_info = info
                            tmp_infos.append(tmp_info)
                            break

                    if not tmp_info:
                        err = _('no such file %(file_name)s') % {'file_name': file_name}
                        break

            else:
                log.debug('method != POST')

                # choose first file_name by default
                info = infos[0]
                file_name = info['name']
                if not info['status'] == 100:
                    err = _('%(file_name)s is in importing, please wait for seconds...') % {'file_name': file_name}
                tmp_infos.append(info)

            if not err:
                risk_reports, risk_traits, risk_values, risk_ranks, risk_studies = get_risk_values_for_indexpage(tmp_infos, category=['Disease'])

                # translate to Japanese
                if browser_language == 'ja':
                    risk_traits = [TRAITS2JA.get(trait) for trait in risk_traits]
            break

        return direct_to_template(request, 'risk_report/show_all.html',
                                  dict(msg=msg, err=err, infos=infos, tmp_infos=tmp_infos,
                                       risk_reports=risk_reports, risk_traits=risk_traits, risk_values=risk_values, risk_studies=risk_studies))


def get_risk_infos_for_subpage(user_id, file_name, trait_name=None, study_name=None):
    msg, err = '', ''
    infos, tmp_info, tmp_risk_store  = None, None, None
    RR_list, RR_list_real, study_list, snps_list = [], [], [], []
    browser_language = get_language()

    with pymongo.Connection(port=settings.MONGO_PORT) as connection:
        data_info = connection['pergenie']['data_info']

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


@login_required
def trait(request, file_name, trait):
    """Show risk value by studies, for each trait.
    """

    user_id = request.user.username
    risk_infos = get_risk_infos_for_subpage(user_id, file_name, trait)
    trait_eng = JA2TRAITS.get(trait, trait)
    risk_infos.update(dict(file_name=file_name,
                           trait_eng=trait_eng,
                           wiki_url_en=TRAITS2WIKI_URL_EN.get(trait_eng),
                           is_ja=bool(get_language() == 'ja')))

    return direct_to_template(request, 'risk_report/trait.html', risk_infos)


@login_required
def study(request, file_name, trait, study_name):
    """Show RR by rss, for each study.
    """
    user_id = request.user.username
    risk_infos = get_risk_infos_for_subpage(user_id, file_name, trait_name=trait, study_name=study_name)
    trait_eng = JA2TRAITS.get(trait, trait)
    risk_infos.update(dict(file_name=file_name,
                           trait_eng=trait_eng,
                           wiki_url_en=TRAITS2WIKI_URL_EN.get(trait_eng),
                           is_ja=bool(get_language() == 'ja')))

    return direct_to_template(request, 'risk_report/study.html', risk_infos)
