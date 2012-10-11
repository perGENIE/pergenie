#!/usr/bin/env python2.7
# -*- coding: utf-8 -*- 

import argparse
import sys
import os
import math

import pymongo
try:
   import cPickle as pickle
except ImportError:
   import pickle

import colors
import weblio_eng2ja
import search_variants

from pprint import pprint

HAPMAP_PORT = 10002
POPULATION_CODE = ['ASW', 'CEU', 'CHB', 'CHD', 'GIH', 'JPT', 'LWK', 'MEX', 'MKK', 'TSI', 'YRI']
UPLOAD_DIR = '/tmp/pergenie'

def pickle_dump_obj(obj, fout_name):
    with open(fout_name, 'wb') as fout:
        pickle.dump(obj, fout, protocol=2)

def pickle_load_obj(fin_name):
    with open(fin_name, 'rb') as fin:
        obj = pickle.load(fin)
    return obj


def LD_block_clustering(risk_store, population_code):
    """
    LD block (r^2) clustering
    -------------------------
    
    * to avoid duplication of ORs

      * use r^2 from HapMap by populaitons
    
    """

    risk_store_LD_clustered = {}

    uniq_rs1_set = set()
    with open('/Volumes/Macintosh HD 2/HapMap/LD_data/rs1_uniq/ld_CEU.rs1.uniq') as uniq_rs1s:
        for uniq_rs1 in uniq_rs1s:
            uniq_rs1_set.update([int(uniq_rs1.replace('rs', ''))])
    print 'uniq_rs1_set', len(uniq_rs1_set)

    with pymongo.Connection(port=HAPMAP_PORT) as connection:
        db = connection['hapmap']
        ld_data = db['ld_data']
        ld_data_by_population_map = dict(zip(POPULATION_CODE, [ld_data[code] for code in POPULATION_CODE]))

        for trait,rss in risk_store.items():
            rs_LD_block_map = {}
            risk_store_LD_clustered[trait] = {}
            print trait

            trait_rss = set(rss)
            print colors.red('# before trait_rss'), len(trait_rss)
            print trait_rss

            if rss:
                print colors.yellow('# in ld_data (uniq_rs1)'), len(uniq_rs1_set.intersection(trait_rss))

                # fetch LD datas from mongo.hapmap.ld_data.POPULATION_CODE
                trait_ld_datas = ld_data_by_population_map[population_code].find( {'rs1': {'$in': list(trait_rss)} } )

                # LD block clustering
                if trait_ld_datas.count() > 0:
                    for trait_ld_data in trait_ld_datas:

                        # about rs1
                        if not rs_LD_block_map:  # init
                            rs_LD_block_map[trait_ld_data['rs1']] = 1

                        elif not trait_ld_data['rs1'] in rs_LD_block_map:  # new block
                            rs_LD_block_map[trait_ld_data['rs1']] = max(rs_LD_block_map.values()) + 1

                        # about rs2
                        if not trait_ld_data['rs2'] in rs_LD_block_map:
                            if trait_ld_data['rs2'] in trait_rss:
                                rs_LD_block_map[trait_ld_data['rs2']] = rs_LD_block_map[trait_ld_data['rs1']]

#                         print trait_ld_data['rs1'], trait_ld_data['rs2'], rs_LD_block_map

                    print colors.yellow('# in ld_data where r^2 > 0.8 & clusterd'), max(rs_LD_block_map.values())
                    print rs_LD_block_map

                    for rs in trait_rss:
                        if not rs in rs_LD_block_map:
                            rs_LD_block_map[rs] = max(rs_LD_block_map.values()) + 1

                    print colors.blue('# after trait_rss'), max(rs_LD_block_map.values())
        #             for k,v in sorted(rs_LD_block_map.items(), key=lambda x:x[1]):
        #                 print k,v

                    # get one rs from each blocks
                    one_rs_index = [rs_LD_block_map.values().index(i+1) for i in range(max(rs_LD_block_map.values()))]
                    LD_blocked_rss = [rs_LD_block_map.items()[index][0] for index in one_rs_index]
            
                    # save risk records of LD block clusterd rss
                    for rs, catalog_record in rss.items():
#                         print rss
                        if rs in LD_blocked_rss:
                            risk_store_LD_clustered[trait][rs] = catalog_record
#                         else:
#                             print 'filterd out record', catalog_record

                else:
                    risk_store_LD_clustered[trait] = rss

            else:
                risk_store_LD_clustered[trait] = rss

            print 


    return risk_store_LD_clustered


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
        return round({'RR':risk_hom, 'R.':risk_het, '..':risk_ref, 'NA': 1.0}[zygosities], 1), average_population_risk
    except KeyError:
        # print >>sys.stderr, colors.blue('{0} is not hom/het/ref'.format(zygosities))
        return 1.0, average_population_risk


def risk_calculation(catalog_map, variants_map, population_code, sex, user_id, file_name, is_LD_block_clustered, is_log, path_to_pickled_risk_report=None):
    risk_store = {}
    risk_report = {}

    """
    Store risk data
    ---------------

     * there are 1 or more ORs for 1 rs. so we need to choice one of them (prioritization)

    """

#     if path_to_pickled_risk_report:
#         print '[INFO] try to load risk report from {}...'.format(path_to_pickled_risk_report)
#         if os.path.exists(path_to_pickled_risk_report):
#             risk_store, risk_report = pickle_load_obj(path_to_pickled_risk_report)
#             return risk_store, risk_report
            
#         else:
#             print '[WARNING] but does not exist'


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


            # --- previous ---
#             # store records by trait
#             if not record['trait'] in risk_store:
#                 risk_store[record['trait']] = {rs: tmp_risk_data} # initial record

#             else:
#                 if not rs in risk_store[record['trait']]:
#                     risk_store[record['trait']][rs] = tmp_risk_data # initial rs

#                 else:
#                     pass
# #                     print >>sys.stderr, colors.green('same rs record for same trait. {0} {1}'.format(record['trait'], rs))

            # --- current ---
            # TODO: store records by trait by study
#             print record['trait'], record['study'], rs
     
            if not record['trait'] in risk_store:
                risk_store[record['trait']] = {record['study']: {rs: tmp_risk_data}} # initial record

            else:
                if not record['study'] in risk_store[record['trait']]:
                    risk_store[record['trait']][record['study']] = {rs: tmp_risk_data} # after initial record

                else:
                    risk_store[record['trait']][record['study']][rs] = tmp_risk_data

            break


    if is_LD_block_clustered and not population_code == 'unkown':
        risk_store  = LD_block_clustering(risk_store, population_code)
    

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

                risk_store[trait][study][rs]['RR'], risk_store[trait][study][rs]['R'] = _relative_risk_to_general_population(risk_store[trait][study][rs]['catalog_map']['freq'],
                                                                                                                             risk_store[trait][study][rs]['catalog_map']['OR_or_beta'],
                                                                                                                             risk_store[trait][study][rs]['zyg'])


                tmp_value = risk_store[trait][study][rs]['RR']

                if is_log:
                   # log
                   try:
                      tmp_value = math.log10(risk_store[trait][study][rs]['RR'])
                   except ValueError:
                      print 'ValueError', tmp_value
                      if tmp_value == 0.0:
                         tmp_value = -2.0

                if tmp_value:
                   # round
                   tmp_value = round(tmp_value, 3)  #

                   if not trait in risk_report:
                       risk_report[trait] = {study: tmp_value}  # initial
                   else:
                       if not study in risk_report[trait]:
                           risk_report[trait][study] = tmp_value  # after initial
                       else:
                           risk_report[trait][study] *= tmp_value
                           risk_report[trait][study] = round(risk_report[trait][study], 2)



#     # FOR DEBUG ONLY
#     debug_risk_report = {}
#     for trait,value in risk_report.items():
#         if trait in 'Eye color':  # not disease
#             pass
#         else:
# #             if value < 50:
#             debug_risk_report[trait] = value


#     risk_report = debug_risk_report

#     pickle_dump_obj([risk_store, risk_report], os.path.join(UPLOAD_DIR, user_id, '{}_{}.p'.format(user_id, file_name)))

    return risk_store, risk_report


def _main():
    parser = argparse.ArgumentParser(description='e.g. risk_report.py -u demo -f 585.23andme.270.txt -p Europian')
    parser.add_argument('-u', '--user_id', required=True)
    parser.add_argument('-f', '--file_name', required=True)
    parser.add_argument('-p', '--population', required=True, choices=['Asian', 'Europian', 'African', 'Japanese', 'none']) ###
    parser.add_argument('--sex', choices=['male', 'female'])
    parser.add_argument('-L', '--LD_block_clustering', action='store_true')
    args = parser.parse_args()

    # TODO: population mapping
    # ------------------------
    population_map = {'African': ['African'],
                      'Europian': ['European', 'Caucasian'],
                      'Asian': ['Chinese', 'Japanese', 'Asian'],
                      'Japanese': ['Japanese', 'Asian'],
                      'none': ['']}
    population = 'population:{}'.format('+'.join(population_map[args.population]))

    catalog_map, variants_map = search_variants.search_variants(args.user_id, args.file_name, population)


    population_code_map = {'Europian': 'CEU',
                           'Japanese': 'JPT',
                           'none': 'CEU'}
    print args.population, population_code_map[args.population]

    risk_store, risk_report = risk_calculation(catalog_map, variants_map, population_code_map[args.population], args.sex,
                                               args.user_id, args.file_name, args.LD_block_clustering, True,
                                               os.path.join(UPLOAD_DIR, args.user_id, '{}_{}.p'.format(args.user_id, args.file_name)))


#     pprint(risk_store)
#     pprint(risk_report

    # Show risk report (value by study)
    # ----------------
    print
    print 'Risk report:'

    eng2ja = weblio_eng2ja.WeblioEng2Ja('data/eng2ja.txt', 'data/eng2ja_plus.txt')

    for (k,v) in risk_report.items(): # sorted by values
        k_ja = eng2ja.try_get(k)

        for i, (study, value) in enumerate(sorted(v.items(), key=lambda(study,value):(value,study), reverse=True)):
#             if i == 0:  # show max
            value = round(value, 3)
            if value < 1:
                print colors.blue('{0} {1} {2}'.format(k, k_ja, value))
            elif value == 1:
                print colors.black('{0} {1} {2}'.format(k, k_ja, value))
            elif 1 <= value <= 2:
                print colors.yellow('{0} {1} {2}'.format(k, k_ja, value))
            elif 2 < value:
                print colors.red('{0} {1} {2}'.format(k, k_ja, value))



#     # Show risk report
#     # ----------------
#     print
#     print 'Risk report:'

#     eng2ja = weblio_eng2ja.WeblioEng2Ja('data/eng2ja.txt', 'data/eng2ja_plus.txt')

#     for (k,v) in sorted(risk_report.items(), key=lambda(k,v):(v,k), reverse=True): # sorted by values
#         k_ja = eng2ja.try_get(k)
#         v = round(v, 3)
#         if v < 1:
#             print colors.blue('{0} {1} {2}'.format(k, k_ja, v))
#         elif v == 1:
#             print colors.black('{0} {1} {2}'.format(k, k_ja, v))
#         elif 1 <= v <= 2:
#             print colors.yellow('{0} {1} {2}'.format(k, k_ja, v))
#         elif 2 < v:
#             print colors.red('{0} {1} {2}'.format(k, k_ja, v))


#     # Show more detail
#     # ----------------
#     while True:
#         try:
#             raw_query = raw_input('Trait> ')
#         except EOFError:
#             break

#         found_record = risk_store.get(raw_query)
#         if found_record:
#             for (k,v) in sorted(found_record.items(), key=lambda(k,v):(v['catalog_map']['OR_or_beta'],k), reverse=True): # sorted by OR
#                 data = (k,
#                         v['catalog_map']['OR_or_beta'],
#                         v['catalog_map']['freq'],
#                         v['catalog_map']['risk_allele'],
#                         v['variant_map'],
#                         v['zyg'],
#                         v['RR'],
#                         v['R'],
#                         v['catalog_map']['initial_sample_size'],
#                         v['catalog_map']['platform'])

#                 msg = 'rs:{0} OR:{1} freq:{2} risk-allele:{3} genotype:{4} zyg:{5} RR:{6} R:{7} sample:{8} platform:{9}'.format(*data)

#                 if v['variant_map'] == 'na':
#                     print colors.black(msg)
#                 elif v['zyg'] == 'RR':
#                     print colors.red(msg)
#                 elif v['zyg'] == 'R.':
#                     print colors.yellow(msg)
#                 elif v['zyg'] == '..':
#                     print colors.blue(msg)
#                 else:
#                     print 'something err...'

if __name__ == '__main__':
    _main()
