import sys, os
import argparse
import math
from pprint import pprint
import doctest
import pymongo

from utils import clogging
log = clogging.getColorLogger(__name__)

HAPMAP_PORT = 10002
POPULATION_CODE = ['ASW', 'CEU', 'CHB', 'CHD', 'GIH', 'JPT', 'LWK', 'MEX', 'MKK', 'TSI', 'YRI']


def _zyg(genotype, risk_allele):
    """
    >>> _zyg('na', '')
    'NA'
    >>> _zyg('AA', 'A')
    'RR'
    >>> _zyg('AT', 'A')
    'R.'
    >>> _zyg('TT', 'A')
    '..'
    """

    if genotype == 'na':
        return 'NA'

    try:
        return {0:'..', 1:'R.', 2:'RR'}[genotype.count(risk_allele)]
    except TypeError:
        log.warn('genotype?? genotype:{0} risk-allele {1} '.format(genotype, risk_allele))  ###
        return '..'


def _relative_risk_to_general_population(freq, OR, zygosities):
    """
    >>> _relative_risk_to_general_population(0.28, 1.37, 'NA')
    (1.0, 1.22)
    >>> _relative_risk_to_general_population(0.28, 1.37, 'RR')
    (1.5, 1.22)
    >>> _relative_risk_to_general_population(0.28, 1.37, 'R.')
    (1.1, 1.22)
    >>> _relative_risk_to_general_population(0.28, 1.37, '..')
    (0.8, 1.22)
    """

    try:
        prob_hom = freq**2
        prob_het = 2*freq*(1-freq)
        prob_ref = (1-freq)**2

        OR_hom = OR**2
        OR_het = OR
        OR_ref = 1.0

        average_population_risk = prob_hom*OR_hom + prob_het*OR_het + prob_ref*OR_ref

        risk_hom = OR_hom/average_population_risk
        risk_het = OR_het/average_population_risk
        risk_ref = OR_ref/average_population_risk

    except TypeError:
        return 1.0, 1.0  ###

    return round({'RR':risk_hom, 'R.':risk_het, '..':risk_ref, 'NA': 1.0}.get(zygosities, 1.0), 1), round(average_population_risk, 2)


def risk_calculation(catalog_map, variants_map, population, user_id, file_name,
                     is_LD_block_clustered):
    risk_store = {}
    risk_report = {}

    """
    Store risk data
    ---------------

     * there are 1 or more ORs for 1 rs. so we need to choice one of them (prioritization)

    """

    for found_id in catalog_map:
        record = catalog_map[found_id]
        rs = record['rs']
        variant = variants_map[rs]

        while True:
            tmp_risk_data = {'catalog_map': record, 'variant_map': variant, 'zyg': None, 'RR': None}

            # filter out odd records
            if not record['risk_allele'] in ['A', 'T', 'G', 'C']:
#                 print colors.yellow("not record['risk_allele'] in ['A', 'T', 'G', 'C']:"), record['risk_allele'], record['OR_or_beta'], record['trait']
                break

            if not record['freq']:
#                 print colors.yellow("not record['freq']"), record['freq'], record['OR_or_beta'], record['trait']
                break

            try:
                if not float(record['OR_or_beta']) > 1:
#                     print colors.yellow("not float(record['OR_or_beta']) > 1"), record['OR_or_beta'], record['trait']
                    break
            except (TypeError, ValueError):
#                 print colors.yellow("Error with float()"), record['OR_or_beta'], record['trait']
                break

            # --- current ---
            # store records by trait by study

            if not record['trait'] in risk_store:
                risk_store[record['trait']] = {record['study']: {rs: tmp_risk_data}} # initial record

            else:
                if not record['study'] in risk_store[record['trait']]:
                    risk_store[record['trait']][record['study']] = {rs: tmp_risk_data} # after initial record

                else:
                    risk_store[record['trait']][record['study']][rs] = tmp_risk_data

            break


    if is_LD_block_clustered and not population == ['']:
        risk_store  = LD_block_clustering(risk_store, population)


    """
    Calculate risk
    --------------

    * use **cumulative model**
    * zygosities are determied by # of risk alleles

    """

    for trait in risk_store:
        for study in risk_store[trait]:
            for rs in risk_store[trait][study]:
                risk_store[trait][study][rs]['zyg'] = _zyg(risk_store[trait][study][rs]['variant_map'],
                                                           risk_store[trait][study][rs]['catalog_map']['risk_allele'])

                RR, R = _relative_risk_to_general_population(risk_store[trait][study][rs]['catalog_map']['freq'],
                                                                                                                             risk_store[trait][study][rs]['catalog_map']['OR_or_beta'],
                                                                                                                             risk_store[trait][study][rs]['zyg'])

                risk_store[trait][study][rs]['RR'] = RR
                risk_store[trait][study][rs]['R'] = R
                # tmp_value = risk_store[trait][study][rs]['RR']

                #
                # if is_log:
                #     try:
                #         tmp_value = math.log10(risk_store[trait][study][rs]['RR'])
                #     except ValueError:
                #         log.error('ValueError {0}'.format(tmp_value))
                #         if tmp_value == 0.0:
                #             tmp_value = -2.0  # -inf

                # risk_store[trait][study][rs]['RR_real'] = risk_store[trait][study][rs]['RR']
                # risk_store[trait][study][rs]['RR'] = tmp_value

                # if tmp_value:
                if not trait in risk_report:
                    risk_report[trait] = {study: RR}  # initial
                else:
                    if not study in risk_report[trait]:
                        risk_report[trait][study] = RR  # after initial
                    else:
                        #
                        # if is_log:
                        #     risk_report[trait][study] += tmp_value
                        # else:
                        risk_report[trait][study] *= RR

    return risk_store, risk_report

def _test():
    import doctest, risk_report
    doctest.testmod()

if __name__ == '__main__':
    _test()
