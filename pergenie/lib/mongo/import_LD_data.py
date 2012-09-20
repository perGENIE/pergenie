#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import argparse
import os
import sys
import csv
import datetime
import re
import pymongo
import glob

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


def import_LD_data(path_to_LD_data_dir):
    """
    import LD-data into MongoDB
    -----------------------------------

    * input data: HapMap LD-data, generated from HaploView software's .LD and .CHECK outputs for markers up to 200kb apart.

      * genomic coordinate is **hg18**
      * for detailed info, see ftp://ftp.ncbi.nlm.nih.gov/hapmap/ld_data/latest/00README.txt

    """

    with pymongo.Connection() as connection:
        ld_data = connection['pergenie']['ld_data']
        ld_data_by_population_map = dict(zip(POPULATION_CODE, [ld_data[population] in POPULATION_CODE]))
        
        # ensure db.ld_data.POPULATION_CODE does not exist
        for population_code in POPULATION_CODE:
            if ld_data_by_population_map[population_code].find_one():
                connection['pergenie'].drop_collection(ld_data_by_population_map[population_code])
                print '[WARNING] dropped old collection', population_code

        fields = [('pos1', 'Chromosomal position of marker1', _integer),
                  ('pos2', 'Chromosomal position of marker2', _integer),
                  ('population_code', 'population code', _string),
                  ('rs1', 'rs number for marker1', _rs),
                  ('rs2', 'rs number for marker2', _rs),
                  ('d_prime', 'Dprime', _float),
                  ('r_square', 'R square', _float),
                  ('LOD', 'LOD', _float),
                  ('fbin', 'fbin (index based on Col1)', _float)]

        ld_data_files = glob.glob(os.path.join(path_to_LD_data_dir, '*.txt'))
        r = re.compile('ld_chr(\d+)_(...).txt')

        for ld_data_file in ld_data_files:
            print '[INFO] Importing {} ...'.format()
            chrom, population_code = r.findall(ld_data_file)

            with open(ld_data_file, 'rb') as fin:
                for i,record in enumerate(csv.DictReader(fin, delimiter=' ')):
#                     print >>sys.stderr, i
                    data = {}
                    for dict_name, record_name, converter in fields:
                        data[dict_name] = converter(record[record_name])
                    data['chrom'] = chrom

                    # assert population_code == data['population_code'] ?

                    if not text in POPULATION_CODE:
                        print colors.red('[WARNING] not in population code: {}'.format(text))
                    
                    # filtering by r_square ?
                    # -----------------------

                    ld_data_by_population_map[population_code].insert(data)

        # TODO: indexing target
        # ld_data.create_index([('', pymongo.ASCENDING)])

    print '[INFO] # of documents in ld_data (after):', catalog.count()


def _string(text):
    return text

def _integer(text):
    return int(text)

def _float(text):
    return float(text)

# try:


#     except ValueError:
#         print '[WARNING] Failed to convert to float: {}'.format(text)

#         match = re.match('\d*\.\d+', text)
#         if match:
#             return float(match.group())
#         else:
#             return None

def _rs(text):
    return int(text.replace('rs', ''))


def _main():
    parser = argparse.ArgumentParser(description='import gwascatalog.txt to the database')
    parser.add_argument('path_to_LD_data_dir')
    args = parser.parse_args()

    import_LD_data(args.path_to_LD_data_dir)


if __name__ == '__main__':
    _main()
