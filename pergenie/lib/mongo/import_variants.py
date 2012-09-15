#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import argparse
import sys
import os
import subprocess
import csv
import time
import pymongo

import colors

class ParseError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

def import_variants(path_to_variants, population, file_format, user_id):
    """doc"""
    
    with pymongo.Connection() as connection:
        db = connection['pergenie']
        users_variants = db['variants'][user_id][path_to_variants]
        data_info = db['data_info']

        if users_variants.find_one():
            # this variants file is already imported, so drop old one.
            db.drop_collection(users_variants)
            print >>sys.stderr, '[INFO] dropped old collection of {}'.format(path_to_variants)

        # print '[INFO] Countiong input lines ...',
        # file_lines = int(subprocess.check_output(['wc', '-l', ]).split()[0])
        # print 'done. # of lines: {0}'.format(file_lines)

        print >>sys.stderr, '[INFO] Importing {} ...'.format(path_to_variants)
        prev_collections = db.collection_names()

        try:
            with open(path_to_variants, 'rb') as fin:
                for data in parse_lines(fin, file_format):
                    if data['rs']:
                        users_variants.insert(data)

                #
                call_file_name = os.path.basename(path_to_variants)
                print 'call_file_name', call_file_name
                print 'find', data_info.find({'user_id': user_id, 'name': call_file_name})

                # TODO: rewrite to use $inc
                data_info.update({'user_id': user_id, 'name': call_file_name}, {"$set": {'status': 90.0}})

                print >>sys.stderr,'[INFO] ensure_index ...'
                users_variants.ensure_index('rs', unique=True)  # ok?

                #
                data_info.update({'user_id': user_id, 'name': call_file_name}, {"$set": {'status': 100.0}})

                print >>sys.stderr,'[INFO] done. added collection {}'.format(set(db.collection_names()) - set(prev_collections))
            return None

        except ParseError, e:
            print '[ERROR] ParseError:', e.value
            return e.value


def parse_lines(handle, file_format):
    """
    23andme:
    # rsid chromosome position genotype

    tmmb:
    chromosome position rsid reference genotype1 genotype2
    """

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
                                       ('genotype2', 'genotype2', _string)],
                            'delimiter': '\t'}
                  }
    parse_map = parse_maps[file_format]

    # start = time.time()

    # Paser header lines, if infile have header
    if parse_map['header_chr']:
        for line in handle:
            if not line.startswith(parse_map['header_chr']):
                raise ParseError, 'uploaded file has no header line. format correct?'

            elif line.startswith(parse_map['header_starts']):
                break

    # Parse record lines by fieldnames
    fieldnames = [x[1] for x in parse_map['fields']]
    for record in csv.DictReader(handle, fieldnames=fieldnames, delimiter=parse_map['delimiter']):
        data = {}
        for dict_name, record_name, converter in parse_map['fields']:
            try:
                data[dict_name] = converter(record.get(record_name, None))
            except ParseError:
                data[dict_name] = None
                data['info'] = record.get(record_name, None)
            
        yield data


def _rs(text):
    if text:
        try:
            return  int(text.replace('rs', ''))
        except ValueError:
            raise ParseError, '[WARNING] rs? {}'

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
    parser.add_argument('path_to_variants')
    parser.add_argument('population')
    parser.add_argument('file_format')
    parser.add_argument('user_id')
    args = parser.parse_args()

    import_variants(args.path_to_variants, args.population, args.file_format, args.user_id)


if __name__ == '__main__':
    _main()
