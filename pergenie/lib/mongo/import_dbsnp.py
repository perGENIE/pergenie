# -*- coding: utf-8 -*-

import sys
import subprocess
import argparse
import csv
from pymongo import MongoClient, ASCENDING


def import_dbsnp(settings):
    """Import VCF formatted dbSNP into MongoDB.

    * VCF formatted dbSNP file is available from Broad Institute's FTP site.
      ftp://gsapubftp-anonymous@ftp.broadinstitute.org/bundle/1.2/b37/dbsnp_132.b37.vcf.gz

    * Notes:
      * collection size for dbsnp_132.b37.vcf (4.3GB) is approximately 16GB
      * This function is independent from Django.
    """

    path_to_dbsnp = settings.PATH_TO_DBSNP
    db_name = 'dbsnp'
    collection_name = settings.DBSNP_VERSION
    is_snp_only = False

    SNP_tag = {'B132': 'SNP',
               'B137': 'SNV'}[collection_name]

    with MongoClient(host=settings.MONGO_URI) as c:
        dbsnp = c[db_name][collection_name]

        # ensure old collections does not exist
        if dbsnp.find_one():
            c[db_name].drop_collection(collection_name)
            print 'Dropped old collection.'
        assert dbsnp.count() == 0

        print 'Counting input lines ...',
        file_lines = int(subprocess.Popen(['wc', '-l', path_to_dbsnp], stdout=subprocess.PIPE).communicate()[0].split()[0])
        print 'done. # of lines:', file_lines

        fields = [('chrom', '#CHROM', _string),
                  ('pos', 'POS', _integer),
                  ('rs', 'ID', _rsid),
                  ('ref', 'REF', _string),
                  ('alt', 'ALT', _alt),
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
            print 'done. Field:', fieldnames

            print 'Importing', path_to_dbsnp
            for i,record in enumerate(csv.DictReader(fin, fieldnames=fieldnames, delimiter='\t')):
                data = {}
                for dict_name, record_name, converter in fields:
                    data[dict_name] = converter(record[record_name])

                if is_snp_only:
                    if data['info'].get('VC') != SNP_tag:
                        continue

                dbsnp.insert(data)
                record_count += 1

                if i>0 and i%100000 == 0:
                    print '{0}% done. {1} records imported.'.format(round(float(i)/float(file_lines),3)*100, record_count)

        print '100.0% done. {0} records imported.'.format(record_count)

        print 'Creating index for rsid ...',
        dbsnp.create_index([('chrom', ASCENDING), ('pos', ASCENDING)])
        dbsnp.create_index([('rs', ASCENDING)])
        dbsnp.create_index([('info', ASCENDING)])
        print 'done.'


def _integer(text):
    return int(text)

def _string(text):
    return text

def _alt(text):
    return text.split(',')[0]

def _rsid(text):
    try:
        return int(text.replace('rs',''))
    except ValueError:
        if len(text.split(';')) > 1: # rs55764002;rs60046810;... -> rs55764002
            first_rs = text.split(';')[0]
#             print '{0} -> {1}'.format(text, first_rs)
            return int(first_rs.replace('rs',''))

def _info(text):
    infos = dict()

    for info in text.split(';'):
        tmp = info.split('=')

        if len(tmp) == 1:
            infos.update({tmp[0]: True})
        else:
            try:
                infos.update({tmp[0]: float(tmp[1])})
            except ValueError:
                infos.update({tmp[0]: tmp[1]})

    return infos
