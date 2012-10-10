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

UPLOAD_DIR = '/tmp/pergenie'

class VariantParseError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

def import_variants(file_name, population, file_format, user_id):
    """doc"""
    
    with pymongo.Connection() as connection:
        db = connection['pergenie']
        users_variants = db['variants'][user_id][file_name]
        data_info = db['data_info']
        data_info.update({'user_id': user_id, 'name': file_name}, {"$set": {'status': 1}})
 
        # ensure this variants file is not imported
        if users_variants.find_one():
            db.drop_collection(users_variants)
            print >>sys.stderr, '[WARNING] dropped old collection of {}'.format(file_name)

        variant_file_path = os.path.join(UPLOAD_DIR, user_id, file_name)
        print '[INFO] variant_file_path:', variant_file_path

        print '[INFO] Countiong input lines ...',
        file_lines = int(subprocess.check_output(['wc', '-l', variant_file_path]).split()[0])
        print 'done. # of lines: {}'.format(file_lines)

        print >>sys.stderr, '[INFO] Start importing {} ...'.format(file_name)
        prev_collections = db.collection_names()

        try:
            with open(variant_file_path, 'rb') as fin:
                for i,data in enumerate(parse_lines(fin, file_format)):
                    if data['rs']:
                        users_variants.insert(data)

                    if i>0 and i%10000 == 0:
                        upload_status = int( 100 * ( i*0.9 / file_lines ) + 1 )
                        data_info.update({'user_id': user_id, 'name': file_name}, {"$set": {'status': upload_status}})
                        print '[INFO] status: {}'.format(data_info.find({'user_id': user_id, 'name': file_name})[0]['status'])  #

                print >>sys.stderr,'[INFO] ensure_index ...'
                users_variants.ensure_index('rs', unique=True)  # ok?

                data_info.update({'user_id': user_id, 'name': file_name}, {"$set": {'status': 100}})

                print >>sys.stderr,'[INFO] done. added collection {}'.format(set(db.collection_names()) - set(prev_collections))
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
    parser.add_argument('file_name')
    parser.add_argument('population')
    parser.add_argument('file_format')
    parser.add_argument('user_id')
    args = parser.parse_args()

    import_variants(args.file_name, args.population, args.file_format, args.user_id)


if __name__ == '__main__':
    _main()
