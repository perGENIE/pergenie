#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import sys
import subprocess
import argparse
import csv

from pymongo import MongoClient, ASCENDING

def import_dbsnp(path_to_dbsnp, db_name, collection_name, is_snp_only=False, port=27017):
    """Import VCF formatted dbSNP into MongoDB.

    * VCF formatted dbSNP file is available from Broad Institute's FTP site.
      ftp://gsapubftp-anonymous@ftp.broadinstitute.org/bundle/1.2/b37/dbsnp_132.b37.vcf.gz

    * Notes:
      * collection size for dbsnp_132.b37.vcf (4.3GB) is approximately 16GB
      * This function is independent from Django.
    """

    SNP_tag = 'VC=' + {'B132': 'SNP',
                       'B137': 'SNV'}[collection_name]

    with MongoClient(port=port) as c:
        dbsnp = c[db_name][collection_name]

        # ensure old collections does not exist
        if dbsnp.find_one():
            c[db_name].drop_collection(collection_name)
            print 'Dropped old collection.'
        assert dbsnp.count() == 0

        print 'Counting input lines ...',
        file_lines = int(subprocess.check_output(['wc', '-l', path_to_dbsnp]).split()[0])
        print 'done. # of lines: {0}'.format(file_lines)

        fields = [('chrom', '#CHROM', _string),
                  ('pos', 'POS', _integer),
                  ('rs', 'ID', _rsid),
                  ('ref', 'REF', _string),
                  ('alt', 'ALT', _string),
                  ('info', 'INFO', _info)]

        record_count = 0
        with open(path_to_dbsnp, 'rb') as fin:
            print 'Determining fieldnames of records ...',
            for line in fin:
                if not line.startswith('#'):
                    sys.exit('[ERROR] Input does not have vcf-header lines.')
                elif line.startswith('#CHROM'):
                    fieldnames = line.strip().split('\t')
                    break
            print 'done. Field: {}'.format(fieldnames)

            print 'Importing {} ...'.format(path_to_dbsnp)
            for i,record in enumerate(csv.DictReader(fin, fieldnames=fieldnames, delimiter='\t')):
                data = {}
                for dict_name, record_name, converter in fields:
                    data[dict_name] = converter(record[record_name])

                if is_snp_only:
                    if not SNP_tag in data['info']:
                        continue

                dbsnp.insert(data)
                record_count += 1

                if i>0 and i%100000 == 0:
                    print '{0}% done. {1} records imported.'.format(round(float(i)/float(file_lines),3)*100, record_count)

        print '100.0% done. {0} records imported.'.format(record_count)

        print 'Creating index for rsid ...',
        dbsnp.create_index([('chrom', ASCENDING), ('pos', ASCENDING)])
        dbsnp.create_index([('rs', ASCENDING)])

        print 'done.'


def _integer(text):
    return int(text)

def _string(text):
    return text

def _rsid(text):
    try:
        return int(text.replace('rs',''))
    except ValueError:
        if len(text.split(';')) > 1: # rs55764002;rs60046810;... -> rs55764002
            first_rs = text.split(';')[0]
#             print '{0} -> {1}'.format(text, first_rs)
            return int(first_rs.replace('rs',''))

def _info(text):
    return [info_tag for info_tag in text.split(';')]


def _main():
    parser = argparse.ArgumentParser(description='Import dbsnp.vcf to MongoDB')
    parser.add_argument('path_to_dbsnp', help='path to dbsnp.vcf, e.g., dbsnp_132.b37.vcf')
    parser.add_argument('db_name', help='db name, e.g., dbsnp')
    parser.add_argument('collection_name', help='collection name, e.g., B132')
    parser.add_argument('--snp_only', action='store_true', help='Import SNPs only (Do not import INDELs).')
    parser.add_argument('--port', type=int)
    args = parser.parse_args()

    import_dbsnp(args.path_to_dbsnp, args.db_name, args.collection_name, args.snp_only, args.port)

if __name__ == '__main__':
    _main()
