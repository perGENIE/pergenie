#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import argparse
import os
import sys
import csv
import time
import datetime
import re
import subprocess
import glob

import pymongo
import colors

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


def import_LD_data(path_to_LD_data_dir, mongo_port):
    """
    import LD-data into MongoDB
    -----------------------------------

    * input data: HapMap LD-data, generated from HaploView software's .LD and .CHECK outputs for markers up to 200kb apart.

      * genomic coordinate is **hg18**
      * for detailed info, see ftp://ftp.ncbi.nlm.nih.gov/hapmap/ld_data/latest/00README.txt

    """

    print '[INFO]', datetime.datetime.now()

    with pymongo.Connection(port=mongo_port) as connection:
        db = connection['hapmap']
        ld_data = db['ld_data']
        ld_data_by_population_map = dict(zip(POPULATION_CODE, [ld_data[population_code] for population_code in POPULATION_CODE]))
        
        # ensure db.ld_data.POPULATION_CODE does not exist
        for population_code in POPULATION_CODE:
            if ld_data_by_population_map[population_code].find_one():
                connection['pergenie'].drop_collection(ld_data_by_population_map[population_code])
                print '[WARNING] dropped old collection for {0}: {1}'.format(population_code, ld_data_by_population_map[population_code])

        print '[INFO] collections:', db.collection_names()

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

        ld_data_files = glob.glob(os.path.join(path_to_LD_data_dir, 'ld_*.txt'))
        r = re.compile('ld_chr(\d+)_(...).txt')

        for ld_data_file in ld_data_files:
            print '[INFO] Counting input lines ...',
            file_lines = int(subprocess.check_output(['wc', '-l', ld_data_file]).split()[0])
            print 'done. {} lines'.format(file_lines)

            print '[INFO] Importing {} ...'.format(ld_data_file)
            chrom, population_code = r.findall(ld_data_file)[0]

            record_count = 0
            with open(ld_data_file, 'rb') as fin:
                for i,record in enumerate(csv.DictReader(fin, delimiter=' ', fieldnames=fieldnames)):
                    data = {}
                    for dict_name, record_name, converter in fields:
                        data[dict_name] = converter(record[record_name])
                    data['chrom'] = chrom

                    if not data['population_code'] in POPULATION_CODE:
                        print colors.red('[WARNING] not in population code: {}'.format(text))

                    # filtering by r_square                    
                    if data['r_square'] >= 0.8:
                        ld_data_by_population_map[population_code].insert(data)
                        record_count += 1

                    if i>0 and i%1000000 == 0:
                        print '[INFO] {}% done.'.format(round(float(i)/float(file_lines),3)*100)

            print '[INFO] {0} of {1} records ({2}%) imported'.format(record_count, file_lines, round(float(record_count)/float(file_lines),3)*100)
            print '[INFO]', datetime.datetime.now()

        # TODO: indexing target
        # ld_data.create_index([('', pymongo.ASCENDING)])

    print '[INFO]', datetime.datetime.now()

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
    parser.add_argument('--port', type=int)
    args = parser.parse_args()

    import_LD_data(args.path_to_LD_data_dir, args.port)


if __name__ == '__main__':
    _main()
