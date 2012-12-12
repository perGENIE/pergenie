#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import argparse
import sys
import os
import subprocess
import csv
import time
import datetime

import pymongo

import colors

class VariantParseError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

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

        # ensure this variants file is not imported
        if users_variants.find_one():
            db.drop_collection(users_variants)
            print >>sys.stderr, colors.yellow('[WARNING] dropped old collection of {}'.format(file_name_cleaned))

        print >>sys.stderr, '[INFO] Countiong input lines ...',
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
        prev_collections = db.collection_names()

        try:
            with open(file_path, 'rb') as fin:
                for i,data in enumerate(parse_lines(fin, file_format)):
                    if data['rs']:
                        users_variants.insert(data)

                    if i>0 and i%10000 == 0:
                        upload_status = int( 100 * ( i*0.9 / file_lines ) + 1 )
                        data_info.update({'user_id': user_id, 'name': file_name_cleaned}, {"$set": {'status': upload_status}})
                        print '[INFO] status: {}'.format(data_info.find({'user_id': user_id, 'name': file_name_cleaned})[0]['status'])

                print >>sys.stderr,'[INFO] ensure_index ...'
                users_variants.ensure_index('rs', unique=True)  # ok?

                data_info.update({'user_id': user_id, 'name': file_name_cleaned}, {"$set": {'status': 100}})

                print >>sys.stderr, '[INFO] status: {}'.format(data_info.find({'user_id': user_id, 'name': file_name_cleaned})[0]['status'])
                print >>sys.stderr, '[INFO] done. added collection {}'.format(set(db.collection_names()) - set(prev_collections))
            return None

        except VariantParseError, e:
            print '[ERROR] VariantParseError:', e.value
            db.drop_collection(users_variants)
            return e.value


def parse_lines(handle, file_format):
    """
    23andme:
    # rsid chromosome position genotype

    tmmb:
    chromosome position rsid reference genotype1 genotype2
    """

    ref_genome_version = None
    parse_maps = {'andme' : {'header_chr': '#',
                             'header_starts': '# rsid',
                             'fields': [('rs', 'rsid', _rs),
                                        ('chrom', 'chromosome', _chrom),
                                        ('pos', 'position', _integer),
                                        ('genotype', 'genotype', _string)],
                             'delimiter': '\t'},
                  'tmmb' : {'header_chr': '',
                            'header_starts': '',
                            'fields': [('chrom', 'chromosome', _chrom),
                                       ('pos', 'position', _integer),
                                       ('rs', 'rsid', _rs),
                                       ('ref', 'reference', _string),
                                       ('genotype1', 'genotype1', _string),
                                       ('genotype2', 'genotype2', _string),
                                       ('genotype', 'genotype', _string)],
                            'delimiter': '\t'}
                  }
    parse_map = parse_maps[file_format]

    # parse headers
    if parse_map['header_chr']:
        for line in handle:
            if not line.startswith(parse_map['header_chr']):
                raise ParseError, 'Uploaded file has no header lines. File format correct?'

            elif line.startswith(parse_map['header_starts']):
                break

            # TODO: infer ref_genome_version
            if file_format == 'andme':
                if 'build 36' in line:
                    ref_genome_version = 'b36'
                elif 'build 37' in line:
                    ref_genome_version = 'b37'
            

    # Parse record lines by fieldnames
    fieldnames = [x[1] for x in parse_map['fields']]
    for record in csv.DictReader(handle, fieldnames=fieldnames, delimiter=parse_map['delimiter']):
        data = {}
        for dict_name, record_name, converter in parse_map['fields']:
            try:
                data[dict_name] = converter(record.get(record_name, None))
            except VariantParseError:
                data[dict_name] = None
                data['info'] = record.get(record_name, None)
            
        if file_format == 'tmmb':
            data['genotype'] = data['genotype1'] + data['genotype2']
            
        yield data


def _rs(text):
    if text:
        try:
            return  int(text.replace('rs', ''))
        except ValueError:
            raise VariantParseError, '[WARNING] rs? {}'

    return None


def _chrom(text):
    chroms = [str(i+1) for i in range(22)] + ['X', 'Y', 'MT', 'M']
    if text:
        try:
            chrom= text.replace('chr', '')
            if not chrom in chroms:
                msg =  '[WARNING] chrom? {}'
                print >>sys.stderr, colors.red(msg.format(text))
            return chrom
        except ValueError:
            msg =  '[WARNING] chrom? {}'
            print >>sys.stderr, colors.red(msg.format(text))
            return chrom
    return None


def _integer(text):
    if text:
        try:
            return int(text)
        except ValueError:
            msg =  '[WARNING] integer? {}'
            print >>sys.stderr, colors.red(msg.format(text))
            return None
    return None


def _string(text):
    return text


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
        print colors.blue('[INFO] import {}'.format(file_path))
        import_variants(file_path, args.population, args.sex, args.file_format, args.user_id, args.mongo_port)

if __name__ == '__main__':
    _main()
