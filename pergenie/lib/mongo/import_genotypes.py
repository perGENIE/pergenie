import sys
import os
import subprocess

from django.conf import settings
from pymongo import MongoClient
import vcf

# from lib.parser import andmeParser  # TODO:
from apps.genome.models import Genome
from utils import clogging
log = clogging.getColorLogger(__name__)


def count_line(file_path):
    return int(subprocess.Popen(['wc', '-l', file_path], stdout=subprocess.PIPE).communicate()[0].split()[0])

def import_genotypes(genome, drop_old_collections=True, minimum_snps=False):
    """Import genotype data into MongoDB.

    Args:
    - genome: a Genome model instance
    """

    file_path = os.path.join(settings.UPLOAD_DIR,
                             str(genome.owner.id),
                             str(genome.id))

    log.info('Counting lines...')
    file_lines = count_line(file_path)
    log.info('#lines: {}'.format(file_lines))

    with MongoClient(host=settings.MONGO_URI) as con:
        db = con[settings.MONGO_DB_NAME]
        genotypes = db[str(genome.id)]

        if drop_old_collections and genotypes.find_one():
            db.drop_collection(genotypes)
            log.warn('Dropped old collection.')

        log.info('Start importing...')

        # TODO:
        # if minimum_snps:
        #     uniq_snps = set(gwascatalog.get_uniq_snps_list())

        with open(file_path, 'rb') as fin:
            try:
                reader = {Genome.FILE_FORMAT_VCF: vcf.DictReader}[genome.file_format]

                for i,record in enumerate(reader(fin)):

                    if genome.file_format == Genome.FILE_FORMAT_VCF:
                        record['genotype'] = record['genotypes'][record['samples'][0]]

                    if data['rs']:
                        # Minimum import
                        # if minimum_snps:
                        #     if not data['rs'] in uniq_snps:
                        #         continue

                        # TODO: rs => snp_id
                        # TODO: genotype => alleles
                        genotypes.insert_one({'rs': record['rs'],
                                              'genotype': record['genotype']})

                    if i > 0 and i % 10000 == 0:
                        log.debug('{i} lines done...'.format(i=i+1))

                        # Update Genome status
                        status = int(100 * (i * 0.9 / file_lines) + 1)
                        genome.status = status
                        genome.save()

            except Exception, e:
                log.error('Error: {}'.format(str(e)))
                db.drop_collection(genotypes)
                genome.status = '-1'
                genome.save()
                return e  # FIXME

            # TODO:
            log.info('Creating index...')
            genotypes.create_index('rs')

            genome.status = 100
            genome.save()

            log.info('Done!')

            return
