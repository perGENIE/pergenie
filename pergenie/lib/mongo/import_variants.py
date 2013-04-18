#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import sys
import os
import subprocess
import datetime
import argparse

import pymongo

from VCFParser import VCFParser, VCFParseError
from andmeParser import andmeParser, andmeParseError


def import_variants(file_path, population, sex, file_format, user_id, mongo_port=27017):
    """doc"""

    # remove dots from file_name
    file_name = file_path.split('/')[-1]
    file_name_cleaned = file_name.replace('.', '').replace(' ', '')
    print >>sys.stderr, '[INFO] collection name: {}'.format(file_name_cleaned)

    with pymongo.Connection(port=mongo_port) as connection:
        db = connection['pergenie']
        users_variants = db['variants'][user_id][file_name_cleaned]
        data_info = db['data_info']

        data_info.update({'user_id': user_id, 'name': file_name_cleaned}, {"$set": {'file_name_cleaned': file_name_cleaned}}, upsert=True)

        # ensure this variants file is not imported
        if users_variants.find_one():
            db.drop_collection(users_variants)
            # print >>sys.stderr, colors.yellow('[WARNING] dropped old collection of {}'.format(file_name_cleaned))

        print >>sys.stderr, '[INFO] Countiong input lines ...',
        print >>sys.stderr, '[INFO] {}'.format(file_path)
        file_lines = int(subprocess.check_output(['wc', '-l', file_path]).split()[0])
        print >>sys.stderr, 'done. # of lines: {}'.format(file_lines)


        today = str(datetime.datetime.today()).replace('-', '/')
        info = {'user_id': user_id,
                'name': file_name_cleaned,
                'raw_name': file_name,
                'date': today,
                'population': population,
                'sex': sex,
                'file_format': file_format,
                'status': float(1.0)}

        data_info.update({'user_id': user_id, 'name': file_name_cleaned}, {"$set": info}, upsert=True)

        print >>sys.stderr,'[INFO] Start importing {0} as {1}...'.format(file_name, file_name_cleaned)

        print '[INFO] file_path:', file_path
        print '[INFO] file_format:', file_format

        prev_collections = db.collection_names()

        # Parse lines
        with open(file_path, 'rb') as fin:
            try:
                p = {'vcf': VCFParser,
                     'andme': andmeParser}[info['file_format']](fin)

                for i,data in enumerate(p.parse_lines()):
                    if info['file_format'] == 'vcf':
                        # TODO: handling multi-sample .vcf file

                        # currently, choose first sample from multi-sample .vcf
                        tmp_genotypes = data['genotype']
                        data['genotype'] = tmp_genotypes[p.sample_names[0]]

                    if data['rs']:
                        sub_data = {k: data[k] for k in ('chrom', 'pos', 'rs', 'genotype')}
                        users_variants.insert(sub_data)

                    if i > 0 and i % 10000 == 0:
                        upload_status = int(100 * (i * 0.9 / file_lines) + 1)
                        data_info.update({'user_id': user_id, 'name': file_name_cleaned}, {"$set": {'status': upload_status}})

                        tmp_status = data_info.find({'user_id': user_id, 'name': file_name_cleaned})[0]['status']
                        print '[INFO] status: {0}, db.collection.count():{1}'.format(tmp_status, users_variants.count())

                print >>sys.stderr,'[INFO] ensure_index ...'
                users_variants.ensure_index('rs', unique=True)  # ok?

                data_info.update({'user_id': user_id, 'name': file_name_cleaned}, {"$set": {'status': 100}})

                print >>sys.stderr, '[INFO] status: {}'.format(data_info.find({'user_id': user_id, 'name': file_name_cleaned})[0]['status'])
                print >>sys.stderr, '[INFO] done. added collection {}'.format(set(db.collection_names()) - set(prev_collections))
                return None

            except (VCFParseError, andmeParseError), e:
                print '[ERROR] ParseError:', e.error_code
                # data_info.remove({'user_id': user_id})
                data_info.update({'user_id': user_id, 'name': file_name_cleaned}, {"$set": {'status': -1}})
                db.drop_collection(users_variants)
                return e.error_code


    parse_map = parse_maps[file_format]


def _main():
    parser = argparse.ArgumentParser(description='import variants file into mongodb')
    parser.add_argument('--file-paths', metavar='filepath', nargs='+', required=True)
    parser.add_argument('--population', required=True)
    parser.add_argument('--sex', required=True)
    parser.add_argument('--file-format', required=True)
    parser.add_argument('--user-id', required=True)
    parser.add_argument('--mongo-port', default=27017)
    args = parser.parse_args()

    for file_path in args.file_paths:
        # print colors.blue('[INFO] import {}'.format(file_path))
        import_variants(file_path, args.population, args.sex, args.file_format, args.user_id, args.mongo_port)


if __name__ == '__main__':
    _main()
