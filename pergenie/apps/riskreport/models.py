import sys, os
import datetime
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


def get_user_data_infos(user_id):
    c = MongoClient(host=settings.MONGO_URI)
    data_info = c['pergenie']['data_info']

    if user_id.startswith(settings.DEMO_USER_ID): user_id = settings.DEMO_USER_ID

    infos = list(data_info.find({'user_id': user_id}))

    return infos


def get_user_file_info(user_id, file_name):
    c = MongoClient(host=settings.MONGO_URI)
    data_info = c['pergenie']['data_info']

    if user_id.startswith(settings.DEMO_USER_ID): user_id = settings.DEMO_USER_ID

    info = data_info.find_one({'user_id': user_id, 'name': file_name})

    return info


def set_user_last_viewed_file(user_id, file_name):
    c = MongoClient(host=settings.MONGO_URI)
    user_info = c['pergenie']['user_info']
    user_info.update({'user_id': user_id},
                     {"$set": {'last_viewed_file': file_name}}, upsert=True)

def set_user_data_population(user_id, file_name, population):
    c = MongoClient(host=settings.MONGO_URI)
    user_info = c['pergenie']['data_info']

    if user_id.startswith(settings.DEMO_USER_ID): user_id = settings.DEMO_USER_ID

    user_info.update({'user_id': user_id,
                      'name': file_name},
                     {"$set": {'population': population}})

def set_user_viewed_riskreport_showall_done(user_id):
    c = MongoClient(host=settings.MONGO_URI)
    user_info = c['pergenie']['user_info']
    user_info.update({'user_id': user_id},
                     {"$set": {'viewed_riskreport_showall': True}}, upsert=True)


def _import_riskreport(tmp_info):
    c = MongoClient(host=settings.MONGO_URI)

    if tmp_info['user_id'].startswith(settings.DEMO_USER_ID): tmp_info['user_id'] = settings.DEMO_USER_ID

    # Get GWAS Catalog records for this population
    population = 'population:{0}'.format('+'.join(settings.POPULATION_MAP[tmp_info['population']]))
    catalog_map, variants_map = search_variants.search_variants(user_id=tmp_info['user_id'],
                                                                file_name=tmp_info['name'],
                                                                file_format=tmp_info['file_format'],
                                                                query=population)
    # Get number of uniq studies for this population
    # & Get cover rate of GWAS Catalog for this population

    uniq_studies, uniq_snps = set(), set()
    n_available = 0
    for record in catalog_map.values():
        if not record['pubmed_id'] in uniq_studies:
            uniq_studies.update([record['pubmed_id']])

        if record['snp_id_current'] and record['snp_id_current'] not in uniq_snps:
            uniq_snps.update([record['snp_id_current']])

            if tmp_info['file_format'] == 'vcf_exome_truseq' and record['is_in_truseq']:
                n_available += 1
            elif tmp_info['file_format'] == 'vcf_exome_iontargetseq' and record['is_in_iontargetseq']:
                n_available += 1
            elif tmp_info['file_format'] == 'andme' and record['is_in_andme']:
                n_available += 1

    print 'n_available:', n_available

    n_studies = len(uniq_studies)
    if tmp_info['file_format'] == 'vcf_whole_genome':
        catalog_cover_rate_for_this_population = 100
    else:
        catalog_cover_rate_for_this_population = round(100 * n_available / len(uniq_snps))

    # Calculate risk
    risk_store, risk_reports = risk_report.risk_calculation(catalog_map, variants_map, settings.POPULATION_MAP[tmp_info['population']],
                                                            tmp_info['user_id'], tmp_info['name'], False)
    # print risk_store

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

    for trait, study_level_rank_and_values in risk_reports.items():
        # Get highest reriability study
        studies = list()
        for study, rank_and_values in study_level_rank_and_values.items():
            studies.append(dict(study=study, rank=rank_and_values[0], RR=rank_and_values[1]))
        highest = get_highest_priority_study(studies)

        # Get SNP level infos (RR, genotype, etc...)
        snp_level_records = list()
        for study, snp_level_sotres in risk_store[trait].items():
            for snp, snp_level_sotre in snp_level_sotres.items():
                snp_level_records.append(dict(snp=snp,
                                              RR=snp_level_sotre['RR'],  # snp-level
                                              genotype=snp_level_sotre['variant_map'],  # snp-level
                                              study=study,
                                              rank=study_level_rank_and_values.get(study, ['na'])[0]  # study-level  # FIXME: why key-error occur?
                                          ))

        users_reports.insert(dict(trait=trait,
                                  RR=highest['RR'],
                                  rank=highest['rank'],
                                  highest=highest['study'],
                                  studies=snp_level_records), upsert=True)

    # Update data_info
    data_info = c['pergenie']['data_info']
    data_info.update({'user_id': tmp_info['user_id'], 'name': tmp_info['name'] },
                     {"$set": {'riskreport': datetime.datetime.today(),
                               'n_studies': n_studies,
                               'catalog_cover_rate_for_this_population': catalog_cover_rate_for_this_population}}, upsert=True)

def _to_signed_real(records, is_log=False):
    """
    >>> records = [{'RR': -1.0}, {'RR': 0.0}, {'RR': 0.1}, {'RR': 1.0}]
    >>> print _to_signed_real(records)
    [{'RR': -10.0}, {'RR': 1.0}, {'RR': 1.3}, {'RR': 10.0}]
    """
    results = []

    for record in records:
        tmp_record = record

        if is_log:
            # Convert to real
            tmp_record['RR'] = pow(10, record['RR'])

        # If RR is negative effects, i.e, 0.0 < RR < 1.0,
        # inverse it and minus sign
        if 0.0 < tmp_record['RR'] < 1.0:
            tmp_record['RR'] = -1.0 / record['RR']
        elif tmp_record['RR'] == 0.0:
            tmp_record['RR'] = 1.0
        else:
            tmp_record['RR'] = record['RR']

        tmp_record['RR'] = round(tmp_record['RR'], 1)

        results.append(tmp_record)

    return results


def get_risk_values_for_indexpage(tmp_info, category=[], is_higher=False, is_lower=False, top=None):  # , is_log=True):
    c = MongoClient(host=settings.MONGO_URI)

    if tmp_info['user_id'].startswith(settings.DEMO_USER_ID): tmp_info['user_id'] = settings.DEMO_USER_ID

    # TODO:
    # always upsert (for debug)
    _import_riskreport(tmp_info)
    users_reports = c['pergenie']['reports'][tmp_info['user_id']][tmp_info['name']]

    # get traits, sorted by RR
    founds = list(users_reports.find().sort('RR', DESCENDING))

    # in category (=disease)
    records = [record for record in founds if TRAITS2CATEGORY.get(record['trait'], 'NA') in category]

    records = _to_signed_real(records)

    # filter for is_higher & is_lower as is_ok
    if is_higher:
        is_ok = lambda x: x >= 0.0
    elif is_lower:
        is_ok = lambda x: x <= 0.0
    else:
        is_ok = lambda x: True

    if not top:
        top = 2000

    risk_traits = [record['trait'] for record in records][:int(top)]
    risk_ranks = [record['rank'] for record in records][:int(top)]
    risk_studies = [record['highest'] for record in records][:int(top)]
    risk_values = [round(record['RR'], 1) for record in records if is_ok(record['RR'])][:int(top)]

    return risk_traits, risk_values, risk_ranks, risk_studies


def get_risk_infos_for_subpage(info, trait=None, study=None):
    c = MongoClient(host=settings.MONGO_URI)
    catalog = get_latest_catalog(port=settings.MONGO_PORT)

    if info['user_id'].startswith(settings.DEMO_USER_ID): info['user_id'] = settings.DEMO_USER_ID

    # TODO: check if riskreport.<user>.<file_name> exist and latest in data_info
    users_reports = c['pergenie']['reports'][info['user_id']][info['name']]

    if study and trait:
        record = users_reports.find_one({'trait': trait})
        record['catalog_info'] = catalog.find_one({'study': study})

        # Get SNP infos (RR, genotype, etc...) for *this* stydy.
        snp_records = [rec for rec in record['studies'] if rec['study'] == study]
        for snp_record in snp_records:
            snp_record['catalog_info'] = catalog.find_one({'study': study,
                                                           'snps': snp_record['snp']})
        snp_records = _to_signed_real(snp_records)

        if get_language() == 'ja':
            trait = TRAITS2JA.get(trait, trait)

        return dict(trait=trait, study=study, record=record, snp_records=snp_records)

    # elif not study and trait:
    #     pass
