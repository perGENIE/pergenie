#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import sys
import os
import datetime
import argparse
# from subprocess import check_output  # py27
import subprocess

from termcolor import colored
import pymongo

from common import clean_file_name
from parser.VCFParser import VCFParser, VCFParseError
from parser.andmeParser import andmeParser, andmeParseError

# FIXME:
try:
    from lib.mysql.bioq import Bioq
except ImportError:
    sys.path.insert(0, '../../')
    from mysql.bioq import Bioq


def import_variants(file_path, population, file_format, user_id, settings,
                    mongo_port=27017):
    """Import variants (genotypes) file, into MongoDB.

    * This function is independent from Django.

    * Supported file formats are:
      * SNP array data from 23andMe
      * VCF (Variant Call Format)
    """

    global bq
    bq= Bioq(settings.DATABASES['bioq']['HOST'],
             settings.DATABASES['bioq']['USER'],
             settings.DATABASES['bioq']['PASSWORD'],
             settings.DATABASES['bioq']['NAME'])

    file_name = os.path.basename(file_path)
    file_name_cleaned = clean_file_name(file_name)
    print >>sys.stderr, '[INFO] Input file:', file_path

    print >>sys.stderr, '[INFO] counting lines...'
    # Count input lines for calculating progress of import_variants
    # file_lines = int(check_output(['wc', '-l', file_path]).split()[0])  # py27
    file_lines = int(subprocess.Popen(['wc', '-l', file_path], stdout=subprocess.PIPE).communicate()[0].split()[0])  # py26
    print >>sys.stderr, '[INFO] #lines:', file_lines

    with pymongo.Connection(port=mongo_port) as con:
        db = con['pergenie']
        users_variants = db['variants'][user_id][file_name_cleaned]
        data_info = db['data_info']

        # Ensure that this variants file has not been imported
        if users_variants.find_one():
            db.drop_collection(users_variants)
            print >>sys.stderr, colored('[WARN] Dropped old collection of {0}'.format(file_name_cleaned), 'yellow')

        info = {'user_id': user_id,
                'name': file_name_cleaned,
                'raw_name': file_name,
                'date': datetime.datetime.today(),
                'population': population,
                # 'sex': sex,
                'file_format': file_format,
                'status': float(1.0)}

        data_info.update({'user_id': user_id, 'name': file_name_cleaned},
                         {"$set": info}, upsert=True)

        prev_collections = db.collection_names()

        print >>sys.stderr,'[INFO] Start importing ...'

        with open(file_path, 'rb') as fin:
            try:
                p = {'vcf_whole_genome': VCFParser,
                     'vcf_exome_truseq': VCFParser,
                     'andme': andmeParser}[info['file_format']](fin)

                for i,data in enumerate(p.parse_lines()):
                    if info['file_format'] in ('vcf_whole_genome', 'vcf_exome_truseq'):
                        # TODO: handling multi-sample .vcf file
                        # currently, choose first sample from multi-sample .vcf
                        tmp_genotypes = data['genotype']
                        data['genotype'] = tmp_genotypes[p.sample_names[0]]

                    print data
                    if not data['rs']:
                        # TODO: try to get rsid from chrom & pos
                        data['rs'] = bq.get_rs(data['chrom'], data['pos'])
                    print data['rs']

                    if data['rs']:
                        # sub_data = {k: data[k] for k in ('chrom', 'pos', 'rs', 'genotype')}  # py27
                        sub_data = dict((k, data[k]) for k in ('chrom', 'pos', 'rs', 'genotype'))  # py26
                        users_variants.insert(sub_data)

                    if i > 0 and i % 10000 == 0:
                        upload_status = int(100 * (i * 0.9 / file_lines) + 1)
                        data_info.update({'user_id': user_id, 'name': file_name_cleaned},
                                         {"$set": {'status': upload_status}})

                        tmp_status = data_info.find({'user_id': user_id, 'name': file_name_cleaned})[0]['status']
                        if tmp_status % 10 == 0:
                            print '[INFO] status: {0}, db.collection.count(): {1}'.format(tmp_status, users_variants.count())

                print >>sys.stderr,'[INFO] create_index ...'
                users_variants.create_index('rs')# , unique=True)
                users_variants.create_index([('chrom', pymongo.ASCENDING), ('pos', pymongo.ASCENDING)])

                data_info.update({'user_id': user_id, 'name': file_name_cleaned},
                                 {"$set": {'status': 100}})
                print >>sys.stderr, '[INFO] done!'
                print >>sys.stderr, '[INFO] Added collection:', set(db.collection_names()) - set(prev_collections)

                return None

            except (VCFParseError, andmeParseError), e:
                print '[ERROR] ParseError:', e.error_code
                # data_info.remove({'user_id': user_id})
                data_info.update({'user_id': user_id, 'name': file_name_cleaned},
                                 {"$set": {'status': -1}})
                db.drop_collection(users_variants)
                return e.error_code


def _main():
    parser = argparse.ArgumentParser(description='Import variants (genotypes) file, into MongoDB.')
    parser.add_argument('--file-paths', metavar='filepath', nargs='+', required=True)
    parser.add_argument('--population', required=True)
    # parser.add_argument('--sex', required=True)
    parser.add_argument('--file-format', required=True)
    parser.add_argument('--user-id', required=True)
    parser.add_argument('--mongo-port', default=27017)
    args = parser.parse_args()

    for file_path in args.file_paths:
        import_variants(file_path, args.population, args.file_format, args.user_id, args.mongo_port)


if __name__ == '__main__':
    _main()
