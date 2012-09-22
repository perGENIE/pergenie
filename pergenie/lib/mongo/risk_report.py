#!/usr/bin/env python2.7
# -*- coding: utf-8 -*- 

import argparse
import sys
import os

import colors
import weblio_eng2ja
import search_variants

from pprint import pprint

def _zyg(genotype, risk_allele):
    if genotype == 'na':
        return 'NA'

    try:
        return {0:'..', 1:'R.', 2:'RR'}[genotype.count(risk_allele)]
    except TypeError:
        print >>sys.stderr, colors.purple('genotype?? genotype:{0} risk-allele {1} '.format(genotype, risk_allele))
        return '..'


def _relative_risk_to_general_population(freq, OR, zygosities):
    try:
        prob_hom = freq**2
        prob_het = freq*(1-freq)
        prob_ref = (1-freq)**2

        OR_hom = OR**2
        OR_het = OR
        OR_ref = 1.0

        average_population_risk = prob_hom*OR_hom + prob_het*OR_het + prob_ref*OR_ref

        risk_hom = OR_hom/average_population_risk
        risk_het = OR_het/average_population_risk
        risk_ref = OR_ref/average_population_risk

        # print 'RR:{0}, R.:{1}, ..:{2}, NA:1.0'.format(round(risk_hom,3), round(risk_het,3), round(risk_ref,3))

    except TypeError:
        # print >>sys.stderr, colors.blue('freq:{0} OR:{1} ...'.format(freq, OR))
        return 1.0

    try: 
        return {'RR':risk_hom, 'R.':risk_het, '..':risk_ref, 'NA': 1.0}[zygosities], average_population_risk
    except KeyError:
        # print >>sys.stderr, colors.blue('{0} is not hom/het/ref'.format(zygosities))
        return 1.0, average_population_risk

def risk_calculation(catalog_map, variants_map):
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
                print colors.yellow("not record['risk_allele'] in ['A', 'T', 'G', 'C']:"), record['risk_allele'], record['OR_or_beta'], record['trait']
                break

            if not record['freq']:
                print colors.yellow("not record['freq']"), record['freq'], record['OR_or_beta'], record['trait']
                break

            try:
                if not float(record['OR_or_beta']) > 1:
                    print colors.yellow("not float(record['OR_or_beta']) > 1"), record['OR_or_beta'], record['trait']
                    break
            except (TypeError, ValueError):
                print colors.yellow("Error with float()"), record['OR_or_beta'], record['trait']
                break            

            # store records
            if not record['trait'] in risk_store:
                risk_store[record['trait']] = {rs: tmp_risk_data} # initial record

            else:
                if not rs in risk_store[record['trait']]:
                    risk_store[record['trait']][rs] = tmp_risk_data # initial rs

                else:
                    print >>sys.stderr, colors.green('same rs record for same trait. {0} {1}'.format(record['trait'], rs))
            break
                    # # Prioritize risk data (1-rs has 1-OR) --------------------------------
                    # if args.priority == 'p-value':
                    #     if risk_store[record['trait']][rs][2] < record['p_value']:
                    #         risk_store[record['trait']][rs] = tmp_risk_data # update


    #
    # TODO: thrs by LD
    # ----------------


    """
    Calculate risk
    --------------

     * use **cumulative model**
     * zygosities are determied by the number of risk allele

    """
    for trait in risk_store:
        for rs in risk_store[trait]:
            risk_store[trait][rs]['zyg'] = _zyg(risk_store[trait][rs]['variant_map'],
                                                risk_store[trait][rs]['catalog_map']['risk_allele'])
            risk_store[trait][rs]['RR'], risk_store[trait][rs]['R'] = _relative_risk_to_general_population(risk_store[trait][rs]['catalog_map']['freq'],
                                                                                                           risk_store[trait][rs]['catalog_map']['OR_or_beta'],
                                                                                                           risk_store[trait][rs]['zyg'])

            if not trait in risk_report:
                risk_report[trait] = risk_store[trait][rs]['RR']
            else:
                risk_report[trait] *= risk_store[trait][rs]['RR']

    return risk_store, risk_report


def _main():
    parser = argparse.ArgumentParser(description='')
    """
    USAGE example:
    risk_report.py -u demo -v /tmp/pergenie/demo/585.23andme.270.txt -p Japanese
    """

    parser.add_argument('-u', '--user_id', required=True)
    parser.add_argument('-f', '--file_name', required=True)
    parser.add_argument('-p', '--population', required=True, choices=['Asian', 'Europian', 'African', 'Japanese', 'none']) ###
    parser.add_argument('--sex')    
    # parser.add_argument('--priority', type=str, default='p-value')
    # parser.add_argument('--eng2ja', default='db/eng2ja.txt')
    # parser.add_argument('--eng2ja_plus', default='db/eng2ja_plus.txt')
    args = parser.parse_args()

    #
    # TODO: population mapping
    # ------------------------
    population_map = {'Asian': ['African'],
                      'Europian': ['European', 'Caucasian'],
                      'African': ['Chinese', 'Japanese', 'Asian'],
                      'Japanese': ['Japanese', 'Asian'],
                      'none': ['']}
    
    population = 'population:{}'.format('+'.join(population_map[args.population]))

    catalog_map, variants_map = search_variants.search_variants(args.user_id, args.file_name, population)
    risk_store, risk_report = risk_calculation(catalog_map, variants_map)


    # Show risk report
    # ----------------
    #
    print
    print 'Risk report:'

    eng2ja = weblio_eng2ja.WeblioEng2Ja('data/eng2ja.txt', 'data/eng2ja_plus.txt')

    for (k,v) in sorted(risk_report.items(), key=lambda(k,v):(v,k), reverse=True): # sorted by values
        k_ja = eng2ja.try_get(k)
        v = round(v, 3)
        if v < 1:
            print colors.blue('{0} {1} {2}'.format(k, k_ja, v))
        elif v == 1:
            print colors.black('{0} {1} {2}'.format(k, k_ja, v))
        elif 1 <= v <= 2:
            print colors.yellow('{0} {1} {2}'.format(k, k_ja, v))
        elif 2 < v:
            print colors.red('{0} {1} {2}'.format(k, k_ja, v))


    # Show more detail
    # ----------------
    while True:
        try:
            raw_query = raw_input('Trait> ')
        except EOFError:
            break

        found_record = risk_store.get(raw_query)
        if found_record:
            for (k,v) in sorted(found_record.items(), key=lambda(k,v):(v['catalog_map']['OR_or_beta'],k), reverse=True): # sorted by OR
                data = (k,
                        v['catalog_map']['OR_or_beta'],
                        v['catalog_map']['freq'],
                        v['catalog_map']['risk_allele'],
                        v['variant_map'],
                        v['zyg'],
                        v['RR'],
                        v['R'],
                        v['catalog_map']['initial_sample_size'],
                        v['catalog_map']['platform'])

                msg = 'rs:{0} OR:{1} freq:{2} risk-allele:{3} genotype:{4} zyg:{5} RR:{6} R:{7} sample:{8} platform:{9}'.format(*data)

                if v['variant_map'] == 'na':
                    print colors.black(msg)
                elif v['zyg'] == 'RR':
                    print colors.red(msg)
                elif v['zyg'] == 'R.':
                    print colors.yellow(msg)
                elif v['zyg'] == '..':
                    print colors.blue(msg)
                else:
                    print 'something err...'

if __name__ == '__main__':
    _main()
