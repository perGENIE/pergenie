# -*- coding: utf-8 -*-

import sys, os
import datetime
from pprint import pformat
from pymongo import MongoClient, ASCENDING, DESCENDING

from django.utils.translation import get_language
from django.conf import settings

from lib.mongo.get_latest_catalog import get_latest_catalog
from lib.mongo.get_traits_infos import get_traits_infos
from lib.mongo.reliability_rank import calc_reliability_rank, get_highest_priority_study
import lib.mongo.search_variants as search_variants
import lib.mongo.risk_report as risk_report
from utils import clogging
log = clogging.getColorLogger(__name__)

TRAITS, TRAITS2JA, TRAITS2CATEGORY, TRAITS2WIKI_URL_EN = get_traits_infos(as_dict=True)
JA2TRAITS = dict([(v, k) for (k, v) in TRAITS2JA.items()])


def get_user_infos(user_id):
    c = MongoClient(port=settings.MONGO_PORT)
    data_info = c['pergenie']['data_info']
    infos = list(data_info.find({'user_id': user_id}))

    return infos


def get_user_file_info(user_id, file_name):
    c = MongoClient(port=settings.MONGO_PORT)
    data_info = c['pergenie']['data_info']
    info = data_info.find_one({'user_id': user_id, 'name': file_name})

    return info


def _import_riskreport(tmp_info):
    c = MongoClient(port=settings.MONGO_PORT)

    # Get GWAS Catalog records for this population
    population = 'population:{}'.format('+'.join(settings.POPULATION_MAP[tmp_info['population']]))
    catalog_map, variants_map = search_variants.search_variants(user_id=tmp_info['user_id'],
                                                                file_name=tmp_info['name'],
                                                                file_format=tmp_info['file_format'],
                                                                query=population)
    # Get number of uniq studies for this population
    # & Get cover rate of GWAS Catalog for this population

    uniq, n_available = set(), 0
    for record in catalog_map.values():
        if not record['pubmed_id'] in uniq:
            uniq.update([record['pubmed_id']])

        if not tmp_info['file_format'] == 'vcf_whole_genome':
            if record['is_in_{}'.format(tmp_info['file_format'])]:
                n_available += 1

    n_studies = len(uniq)
    if not tmp_info['file_format'] == 'vcf_whole_genome':
        catalog_cover_rate_for_this_population = int(round(100 * n_available / len(catalog_map)))
    else:
        catalog_cover_rate_for_this_population = 100

    # Calculate risk
    risk_store, risk_reports = risk_report.risk_calculation(catalog_map, variants_map, settings.POPULATION_MAP[tmp_info['population']],
                                                            tmp_info['user_id'], tmp_info['name'], False, True)

    # TODO: merge into import_catalog?
    # Set reliability rank
    tmp_risk_reports = dict()
    for trait,studies in risk_reports.items():
        tmp_risk_reports[trait] = {}

        for study,value in studies.items():
            record = risk_store[trait][study].values()[0]['catalog_map']
            r_rank = calc_reliability_rank(record)
            tmp_risk_reports[trait].update({study: [r_rank, value]})
    risk_reports = tmp_risk_reports

    # Import riskreport into MongoDB
    users_reports = c['pergenie']['reports'][tmp_info['user_id']][tmp_info['name']]
    if users_reports.find_one():
        c['pergenie'].drop_collection(users_reports)

    for trait, x in risk_reports.items():
        studies = list()
        for study, y in risk_store[trait].items():
            for snp, z in y.items():
                studies.append(dict(snp=snp,
                                    RR=z['RR'],  # snp-level
                                    genotype=z['variant_map'],  # snp-level
                                    study=study,
                                    rank=x.get(study, ['na'])[0]  # study-level  # FIXME: why key-error occur?
                                ))

        highest = get_highest_priority_study(studies)
        users_reports.insert(dict(trait=trait,
                                  RR=highest['RR'],
                                  rank=highest['rank'],
                                  highest=highest['study'],
                                  studies=studies), upsert=True)

    # Update data_info
    data_info = c['pergenie']['data_info']
    data_info.update({'user_id': tmp_info['user_id'], 'name': tmp_info['name'] },
                     {"$set": {'riskreport': datetime.datetime.today(),
                               'n_studies': n_studies,
                               'catalog_cover_rate_for_this_population': catalog_cover_rate_for_this_population}}, upsert=True)


def get_risk_values_for_indexpage(tmp_info, category=[], is_higher=False, is_lower=False, top=None, is_log=True):
    c = MongoClient(port=settings.MONGO_PORT)

    # TODO:
    # always upsert (for debug)
    _import_riskreport(tmp_info)
    users_reports = c['pergenie']['reports'][tmp_info['user_id']][tmp_info['name']]

    log.debug(users_reports.count())

    # get traits, sorted by RR
    founds = list(users_reports.find().sort('RR', DESCENDING))

    # in category (=disease)
    records = [record for record in founds if TRAITS2CATEGORY.get(record['trait'], 'NA') in category ]

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
        to_log = lambda x: 10 ** x

    if not top:
        top = 2000

    risk_traits = [record['trait'] for record in records][:int(top)]
    risk_ranks = [record['rank'] for record in records][:int(top)]
    risk_studies = [record['highest'] for record in records][:int(top)]
    risk_values = [[round(to_log(record['RR']), 1) for record in records if is_ok(record['RR'])][:int(top)]]

    return risk_traits, risk_values, risk_ranks, risk_studies


def get_risk_infos_for_subpage(info, trait=None, study=None):
    c = MongoClient(port=settings.MONGO_PORT)
    catalog = get_latest_catalog(port=settings.MONGO_PORT)

    # TODO: check if riskreport.<user>.<file_name> exist and latest in data_info
    users_reports = c['pergenie']['reports'][info['user_id']][info['name']]

    if study and trait:
        record = users_reports.find_one({'trait': trait})
        studies_list = [rec for rec in record['studies'] if rec['study'] == study ]

        if get_language() == 'ja':
            trait = TRAITS2JA.get(trait, trait)

        print '==='
        print list(catalog.find({'study': study}))
        print '==='

        return dict(trait=trait, study=study, RR=record['RR'], rank=record['rank'],
                    catalog_infos=list(catalog.find({'study': study})),
                    studies_list=[rec for rec in record['studies'] if rec['study'] == study],
                    snps_list=[rec['snp'] for rec in studies_list],
                    RR_list=[rec['RR'] for rec in studies_list],
                    genotype_list=[rec['genotype'] for rec in studies_list])

    # elif not study and trait:
    #     pass
