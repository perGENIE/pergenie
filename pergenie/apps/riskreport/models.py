import sys, os
from pymongo import MongoClient, ASCENDING, DESCENDING
from django.utils.translation import get_language
from django.conf import settings
from lib.api.gwascatalog import GWASCatalog
gwascatalog = GWASCatalog()
from lib.api.riskreport import RiskReport
riskreport = RiskReport()
from utils import clogging
log = clogging.getColorLogger(__name__)

TRAITS, TRAITS2JA, TRAITS2CATEGORY, TRAITS2WIKI_URL_EN = gwascatalog.get_traits_infos(as_dict=True)
JA2TRAITS = dict([(v, k) for (k, v) in TRAITS2JA.items()])


def get_risk_values_for_indexpage(tmp_info, category=[], is_higher=False, is_lower=False, top=None):
    if tmp_info['user_id'].startswith(settings.DEMO_USER_ID): tmp_info['user_id'] = settings.DEMO_USER_ID

    with MongoClient(host=settings.MONGO_URI) as c:
        # FIXME: always upsert (for debug)
        riskreport.import_riskreport(tmp_info)
        users_reports = c['pergenie']['reports'][tmp_info['user_id']][tmp_info['name']]

        # get traits, sorted by RR
        founds = list(users_reports.find().sort('RR', DESCENDING))

    # in category (=disease)
    records = [record for record in founds if TRAITS2CATEGORY.get(record['trait'], 'NA') in category]
    records = riskreport.to_signed_real(records)

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
    if info['user_id'].startswith(settings.DEMO_USER_ID): info['user_id'] = settings.DEMO_USER_ID
    with MongoClient(host=settings.MONGO_URI) as c:
        catalog = gwascatalog.get_latest_catalog()

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
            snp_records = riskreport.to_signed_real(snp_records)

            if get_language() == 'ja':
                trait = TRAITS2JA.get(trait, trait)

    return dict(trait=trait, study=study, record=record, snp_records=snp_records)
