import sys, os
from pprint import pprint as pp
import csv
from pymongo import MongoClient, ASCENDING
from django.conf import settings

from extract_region import extract_region
from lib.mysql.bioq import Bioq
bq= Bioq(settings.DATABASES['bioq']['HOST'],
         settings.DATABASES['bioq']['USER'],
         settings.DATABASES['bioq']['PASSWORD'],
         settings.DATABASES['bioq']['NAME'])

from utils import clogging
log = clogging.getColorLogger(__name__)


def import_mycatalog(path_to_mycatalog):
    with MongoClient(host=settings.MONGO_URI) as c:
        db = c['pergenie']
        mycatalog = db['mycatalog']

        if mycatalog.find_one():
            db.drop_collection(mycatalog)

        with open(path_to_mycatalog, 'r') as fin:
            for record in csv.DictReader(fin, delimiter=','):
                record = dict((key.replace(' ', '_'), value) for (key, value) in record.items())
                rs = record['rsid']
                rs2pos_global = bq.get_pos_global(int(rs.replace('rs', '')))
                if not rs2pos_global:
                    log.warn('not found in dbSNP %s' % rs)

                record.update({'chr_id': str(int(rs2pos_global[rs][0:2])),
                               'chr_pos': int(rs2pos_global[rs][2:])})
                assert record['chr_id'] == record['chromosome']

                mycatalog.insert(record)

        # TODO: move to lib.api.*
        # Add region flags like: `is_in_truseq`
        catalog = mycatalog
        n_records, n_truseq, n_andme, n_iontargetseq = 0, 0, 0, 0
        for chrom in [i + 1 for i in range(22)]:
            log.info('Addding flags... chrom: {0}'.format(chrom))

            records = list(catalog.find({'chr_id': str(chrom)}))
            ok_records = [record for record in records if record.has_key('chr_pos')]

            chrom = {23: 'X', 24:'Y'}.get(chrom, chrom)

            # `is_in_truseq`
            region_file = os.path.join(settings.PATH_TO_INTERVAL_LIST_DIR,
                                       'TruSeq-Exome-Targeted-Regions-BED-file.{0}.interval_list'.format(chrom))
            with open(region_file, 'r') as fin:
                extracted = extract_region(region_file, ok_records)
                n_truseq += len(extracted)
                for record in extracted:
                    catalog.update(record, {"$set": {'is_in_truseq': True}})

            # `is_in_andme`
            region_file = os.path.join(settings.PATH_TO_INTERVAL_LIST_DIR,
                                       'andme_region.{0}.interval_list'.format(chrom))
            with open(region_file, 'r') as fin:
                extracted = extract_region(region_file, ok_records)
                n_andme += len(extracted)
                for record in extracted:
                    catalog.update(record, {"$set": {'is_in_andme': True}})

            # `is_in_iontargetseq`
            region_file = os.path.join(settings.PATH_TO_INTERVAL_LIST_DIR,
                                       'Ion-TargetSeq-Exome-50Mb-hg19.{0}.interval_list'.format(chrom))
            with open(region_file, 'r') as fin:
                extracted = extract_region(region_file, ok_records)
                n_iontargetseq += len(extracted)
                for record in extracted:
                    catalog.update(record, {"$set": {'is_in_iontargetseq': True}})

        log.info('`is_in_truseq` extracted:{0}'.format(n_truseq))
        log.info('`is_in_andme` extracted:{0}'.format(n_andme))
        log.info('`is_in_iontargetseq` extracted:{0}'.format(n_iontargetseq))
