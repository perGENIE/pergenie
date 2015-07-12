import sys
import os
import uuid
import datetime
import csv

from django.db import models
from django.conf import settings
from django.utils.translation import ugettext as _

from celery.task import Task
from celery.decorators import task
from celery.exceptions import Ignore
import vcf

from apps.authentication.models import User
from pergenie.mongo import mongo_db

from lib.utils import clogging
from lib.utils.io import count_file_lines
log = clogging.getColorLogger(__name__)


class Genome(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(default=datetime.datetime.now)

    owner = models.ForeignKey(User, related_name='owner')
    readers = models.ManyToManyField(User, related_name='reader')

    file_name = models.FilePathField(max_length=100)
    display_name = models.CharField(max_length=100)

    FILE_FORMAT_VCF = 'VCF'
    FILE_FORMAT_23ANDME = 'ANDME'
    FILE_FORMAT_CHOICES = [
        (FILE_FORMAT_VCF, 'VCF'),
        (FILE_FORMAT_23ANDME, '23andMe CSV'),
    ]
    file_format = models.CharField(max_length=5,
                                   choices=FILE_FORMAT_CHOICES,
                                   default=FILE_FORMAT_VCF)

    POPULATION_ASIAN = 'ASN'
    POPULATION_EUROPEAN = 'EUR'
    POPULATION_AFRICAN = 'AFR'
    POPULATION_JAPANESE = 'JPN'
    POPULATION_UNKNOWN = 'UN'
    POPULATION_CHOICES = [
        (POPULATION_UNKNOWN, _('unknown')),
        (POPULATION_ASIAN, _('Asian')),
        (POPULATION_EUROPEAN, _('European')),
        (POPULATION_AFRICAN, _('African')),
        (POPULATION_JAPANESE, _('Japanese')),
    ]
    population = models.CharField(max_length=3,
                                  choices=POPULATION_CHOICES,
                                  default=POPULATION_UNKNOWN)

    SEX_MALE = 'M'
    SEX_FEMALE = 'F'
    SEX_UNKNOWN = 'U'
    SEX_CHOICES = [
        (SEX_UNKNOWN, _('unknown')),
        (SEX_MALE, _('Male')),
        (SEX_FEMALE, _('Female')),
    ]
    sex = models.CharField(max_length=1,
                           choices=SEX_CHOICES,
                           default=SEX_UNKNOWN)

    status = models.IntegerField(default=0)
    error = models.CharField(max_length=256, blank=True, null=True)

    def get_genome_file(self):
        return os.path.join(settings.UPLOAD_DIR, str(self.owner.id), str(self.id))

    def create_genotypes(self):
        task_import_genotypes.delay(str(self.id))

    def get_genotypes(self):
        return mongo_db['genome-' + str(self.id)]

    def delete_genotypes(self):
        mongo_db.drop_collection(self.get_genotypes())


@task(ignore_result=True)
def task_import_genotypes(genome_id, minimum_snps=False):
    log = Task.get_logger()
    log.info('Importing genotypes...')

    status = 0
    error = None

    try:
        genome = Genome.objects.get(id=uuid.UUID(genome_id))
        genotypes = genome.get_genotypes()

        if genotypes.find_one():
            genome.delete_genotypes()

        file_path = genome.get_genome_file()
        file_lines = count_file_lines(file_path)
        log.info('#lines: {}'.format(file_lines))

        with open(file_path, 'rb') as fin:
            reader = {Genome.FILE_FORMAT_VCF: vcf.DictReader}[genome.file_format]

            log.info('Start importing...')
            for i,record in enumerate(reader(fin)):
                if genome.file_format == Genome.FILE_FORMAT_VCF:
                    record['genotype'] = record['genotypes'][record['samples'][0]]

                if record['rs']:
                    # TODO: rs => snp_id
                    # TODO: genotype => alleles
                    genotypes.insert_one({'rs': record['rs'],
                                          'genotype': record['genotype']})

                if i > 0 and i % 10000 == 0:
                    log.debug('{i} lines done...'.format(i=i+1))

                    # Update Genome status
                    genome.status = int(100 * (i * 0.9 / file_lines) + 1)
                    genome.save()

            log.info('Creating index...')
            genotypes.create_index('rs')
            status = 100

    except csv.Error, csv_error:
        log.info('Parser error:' + str(csv_error))
        error = _('Invalid genome file.')

    except Exception, exception:
        log.error('Unexpected error:' + str(exception))
        erorr = _('Invalid genome file.')

    finally:
        genome.status = status
        genome.error = error

        if error:
            genome.status = -1
            genome.delete_genotypes()

        genome.save()

    log.info('Done!')
