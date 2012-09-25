#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import argparse
import os
import signal
import sys
import csv
import time
import datetime
import re
import subprocess
import glob
from pprint import pprint, pformat
import pymongo

# logging with colors
import logging
from termcolor import colored
import clogging
log = clogging.ColorLogging(logging.getLogger(__name__))
log.setLevel(logging.DEBUG)
stdout = logging.StreamHandler()
stdout.setLevel(logging.DEBUG)
stdout.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
log.addHandler(stdout)


BULK_SIZE = 1000
POPULATION_CODE = ['ASW', 'CEU', 'CHB', 'CHD', 'GIH', 'JPT', 'LWK', 'MEX', 'MKK', 'TSI', 'YRI']
"""
ASW (A): African ancestry in Southwest USA
CEU (C): Utah residents with Northern and Western European ancestry from the CEPH collection
CHB (H): Han Chinese in Beijing, China
CHD (D): Chinese in Metropolitan Denver, Colorado
GIH (G): Gujarati Indians in Houston, Texas
JPT (J): Japanese in Tokyo, Japan
LWK (L): Luhya in Webuye, Kenya
MEX (M): Mexican ancestry in Los Angeles, California
MKK (K): Maasai in Kinyawa, Kenya
TSI (T): Toscans in Italy
YRI (Y): Yoruba in Ibadan, Nigeria (West Africa)
"""


def mongod_pid(command_name, port):
    com1 = subprocess.Popen(['ps'],
                            stdout=subprocess.PIPE,
                            )

    com2 = subprocess.Popen(['grep', command_name],
                            stdin=com1.stdout,
                            stdout=subprocess.PIPE,
                            )

    com3 = subprocess.Popen(['grep', '-v', 'grep'],
                             stdin=com2.stdout,
                             stdout=subprocess.PIPE,
                             )

    end_of_pipe = com3.stdout

    for ps in end_of_pipe:
        print ps,
        if command_name in ps.split(' ') and str(port) in ps.split(' '):
            mongo_pid = int(ps.split(' ')[0])

    return int(mongo_pid)


def import_LD_data(path_to_LD_data_dir, mongo_port,
                   chroms_to_import, populations_to_import, drop_old_collections, ensure_index, skip_import, bulk_insert):
    """
    import LD-data into MongoDB
    -----------------------------------

    * input data: HapMap LD-data, generated from HaploView software's .LD and .CHECK outputs for markers up to 200kb apart.

      * genomic coordinate is **hg18**
      * for detailed info, see ftp://ftp.ncbi.nlm.nih.gov/hapmap/ld_data/latest/00README.txt

    """

    log.info('path_to_LD_data_dir {}'.format(path_to_LD_data_dir))
    log.info('mongo_port{}'.format(mongo_port))
    log.info('chroms_to_import {}'.format(chroms_to_import))
    log.info('populations_to_import {}'.format(populations_to_import))
    log.info('drop_old_collections {}'.format(drop_old_collections))
    log.info('ensure_index {}'.format(ensure_index))
    log.info('skip_import {}'.format(skip_import))
    log.info('bulk_insert {0}, BULK_SIZE {1}'.format(bulk_insert, BULK_SIZE))


    with pymongo.Connection(port=mongo_port) as connection:
        db = connection['hapmap']
        ld_data = db['ld_data']
        ld_data_by_population_map = dict(zip(POPULATION_CODE, [ld_data[code] for code in POPULATION_CODE]))
        
        if drop_old_collections:
            for code in POPULATION_CODE:
                if ld_data_by_population_map[code].find_one():
                    db.drop_collection(ld_data_by_population_map[code])
                    log.warn('dropped old collection for {0}: {1}'.format(code, ld_data_by_population_map[code]))
        log.info('collections {}'.format(db.collection_names()))

        fields = [('pos1', 'Chromosomal position of marker1', _integer),
                  ('pos2', 'Chromosomal position of marker2', _integer),
                  ('population_code', 'population code', _string),
                  ('rs1', 'rs number for marker1', _rs),
                  ('rs2', 'rs number for marker2', _rs),
                  ('d_prime', 'Dprime', _float),
                  ('r_square', 'R square', _float),
                  ('LOD', 'LOD', _float),
                  ('fbin', 'fbin (index based on Col1)', _float)]
        fieldnames = [field[1] for field in fields]

#         if (not chroms_to_import) or (not populations_to_import):
#             ld_data_files = glob.glob(os.path.join(path_to_LD_data_dir, 'ld_*.txt'))
#         else:
        ld_data_files = []
        for population_code in populations_to_import:
            ld_data_files_by_population = [os.path.join(path_to_LD_data_dir, 'ld_chr{0}_{1}.txt'.format(chrom, population_code)) for chrom in chroms_to_import]
            ld_data_files += ld_data_files_by_population
        log.info(pformat(ld_data_files))

        r = re.compile('ld_chr(.+)_(...).txt')

        if not skip_import:
            for ld_data_file in ld_data_files:
                chrom, population_code = r.findall(ld_data_file)[0]
                log.info('chrom:{0} population_code:{1}'.format(chrom, population_code))

                if (not chroms_to_import) or (chrom in chroms_to_import):
                    if (not populations_to_import) or (population_code in populations_to_import):

                        log.info('Counting input lines ...')
                        file_lines = int(subprocess.check_output(['wc', '-l', ld_data_file]).split()[0])
                        log.info('... done. {} lines'.format(file_lines))

                        log.info('Start importing ...')
                        record_count = 0
                        with open(ld_data_file, 'rb') as fin:
                            bulk_data = []
                            for i,record in enumerate(csv.DictReader(fin, delimiter=' ', fieldnames=fieldnames)):
                                data = {}
                                for dict_name, record_name, converter in fields:
                                    data[dict_name] = converter(record[record_name])
                                data['chrom'] = chrom

#                                 if not data['population_code'] in POPULATION_CODE:
#                                     print colors.red('[WARNING] not in population code: {}'.format(text))

#                                 # filtering by r_square
#                                 if data['r_square'] >= 0.8:

                                if bulk_insert:
                                    bulk_data.append(data)
                                    if len(bulk_data) == BULK_SIZE:
                                        ld_data_by_population_map[population_code].insert(bulk_data)
                                        record_count += len(bulk_data)
                                        bulk_data = []

                                else:
                                    ld_data_by_population_map[population_code].insert(data)
                                    record_count += 1
                 
                                if (i+1)>1 and (i+1)%1000000 == 0:
                                    log.info('{0}% done. {1} records to be inserted'.format(round(float(i+1)/float(file_lines),3)*100, i+1))

                        # reminder
                        if bulk_data:
                            ld_data_by_population_map[population_code].insert(bulk_data)
                            record_count += len(bulk_data)
                            bulk_data = []
                            
                        log.info('{0} of {1} records ({2}%) imported'.format(record_count, file_lines, round(float(record_count)/float(file_lines),3)*100))

            log.info('... importing done.')
        

        if ensure_index:
            log.info('Start indexing ...')
            for population_code in POPULATION_CODE:
                ld_data_by_population_map[population_code].ensure_index([('rs1', pymongo.ASCENDING)], drop_dups=True)

            log.info('... indexing done.')

    # kill mongod
    mongo_pid = mongod_pid('mongod', mongo_port)
    log.warn('kill mongod --port {} in 30 seconds. pid:{}'.format(mongo_port, mongo_pid))
    time.sleep(30)
    os.kill(mongo_pid, signal.SIGKILL)
    log.warn('killed {}'.format(mongo_pid))

    log.info('completed!')


def _string(text):
    return text

def _integer(text):
    return int(text)

def _float(text):
    return float(text)

def _rs(text):
    return int(text.replace('rs', ''))


def _main():
    parser = argparse.ArgumentParser(description='import gwascatalog.txt to the database')
    parser.add_argument('path_to_LD_data_dir')
    parser.add_argument('--port', type=int, required=True)

    parser.add_argument('-c', '--chrom', nargs='+', help='population code', required=True)
    parser.add_argument('-p', '--population',  nargs='+', choices=['JPT','CEU'], help='population code', required=True)
    parser.add_argument('--bulk', action='store_true', help='bulk insert')

    parser.add_argument('--new', action='store_true', help='drop old collections')
    parser.add_argument('--skip_import', action='store_true', help='skip inport')
    parser.add_argument('--ensure_index', action='store_true', help='ensure index')
    args = parser.parse_args()

    import_LD_data(args.path_to_LD_data_dir, args.port,
                   args.chrom , args.population, args.new, args.ensure_index, args.skip_import, args.bulk)


if __name__ == '__main__':
    _main()
