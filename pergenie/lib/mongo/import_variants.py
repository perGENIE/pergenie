import sys, os
import datetime
import subprocess
from uuid import uuid4 as uuid
from pymongo import MongoClient, ASCENDING
from common import clean_file_name
from parser.VCFParser import VCFParser, VCFParseError
from parser.andmeParser import andmeParser, andmeParseError
from django.conf import settings
from lib.mysql.bioq import Bioq
bq = Bioq(settings.DATABASES['bioq']['HOST'],
          settings.DATABASES['bioq']['USER'],
          settings.DATABASES['bioq']['PASSWORD'],
          settings.DATABASES['bioq']['NAME'])
from lib.api.gwascatalog import GWASCatalog
gwascatalog = GWASCatalog()
from utils import clogging
log = clogging.getColorLogger(__name__)


def import_variants(file_path, population, file_format, user_id, minimum_import=True):
    """Import variants (genotypes) file, into MongoDB.

    Changelog:

    * minimum import (only import GWAS Catalog SNPs)

    """

    file_name = os.path.basename(file_path)
    file_name_cleaned = clean_file_name(file_name, file_format)
    log.info('Input file: %s' % file_path)

    log.info('counting lines...')
    file_lines = int(subprocess.Popen(['wc', '-l', file_path], stdout=subprocess.PIPE).communicate()[0].split()[0])  # py26
    log.info('#lines: %s' % file_lines)

    with MongoClient(host=settings.MONGO_URI) as con:
        db = con['pergenie']

        # Use UUID for filename
        file_uuid = uuid().hex
        users_variants = db['variants'][file_uuid]

        data_info = db['data_info']

        # Ensure that this variants file has not been imported
        if users_variants.find_one():
            db.drop_collection(users_variants)
            log.warn('Dropped old collection of {0}'.format(file_name_cleaned))

        info = {'file_uuid': file_uuid,
                'user_id': user_id,
                'name': file_name_cleaned,
                'raw_name': file_name,
                'date': datetime.datetime.today(),
                'population': population,
                'file_format': file_format,
                'status': float(1.0)}

        data_info.update({'user_id': user_id, 'name': file_name_cleaned},
                         {"$set": info}, upsert=True)

        prev_collections = db.collection_names()

        log.info('Start importing ...')

        if minimum_import:
            uniq_snps = set(gwascatalog.get_uniq_snps_list())

        with open(file_path, 'rb') as fin:
            try:
                p = {'vcf_whole_genome': VCFParser,
                     'vcf_exome_truseq': VCFParser,
                     'vcf_exome_iontargetseq': VCFParser,
                     'andme': andmeParser}[info['file_format']](fin)

                for i,data in enumerate(p.parse_lines()):
                    if info['file_format'] in [x['name'] for x in settings.FILEFORMATS if x['extention'] == '*.vcf']:
                        # TODO: handling multi-sample .vcf file
                        # currently, choose first sample from multi-sample .vcf
                        tmp_genotypes = data['genotype']
                        data['genotype'] = tmp_genotypes[p.sample_names[0]]

                    if not data['rs']:
                        data['rs'] = bq.get_rs(data['chrom'], data['pos'])

                    if data['rs']:

                        # Minimum import
                        if minimum_import:
                            if not data['rs'] in uniq_snps:
                                continue

                        # sub_data = {k: data[k] for k in ('chrom', 'pos', 'rs', 'genotype')}  # py27
                        sub_data = dict((k, data[k]) for k in ('chrom', 'pos', 'rs', 'genotype'))  # py26
                        users_variants.insert(sub_data)

                    if i > 0 and i % 10000 == 0:
                        upload_status = int(100 * (i * 0.9 / file_lines) + 1)
                        data_info.update({'user_id': user_id, 'name': file_name_cleaned},
                                         {"$set": {'status': upload_status}})

                        tmp_status = data_info.find({'user_id': user_id, 'name': file_name_cleaned})[0]['status']
                        if tmp_status % 10 == 0:
                            log.info('status: {0}, db.collection.count(): {1}'.format(tmp_status, users_variants.count()))

                log.info('create_index ...')
                users_variants.create_index('rs')  # , unique=True)
                users_variants.create_index([('chrom', ASCENDING), ('pos', ASCENDING)])

                data_info.update({'user_id': user_id, 'name': file_name_cleaned},
                                 {"$set": {'status': 95}})
                log.info('done!')
                log.info('Added collection: %s' % (set(db.collection_names()) - set(prev_collections)))

                return

            except (VCFParseError, andmeParseError), e:
                log.error('ParseError: %s' % e.error_code)
                data_info.update({'user_id': user_id, 'name': file_name_cleaned},
                                 {"$set": {'status': -1}})
                db.drop_collection(users_variants)
                return e.error_code
