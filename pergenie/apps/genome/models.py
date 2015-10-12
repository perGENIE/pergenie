import sys
import os
import uuid
import datetime
import csv
import subprocess

from django.db import models
from django.conf import settings
from django.utils.translation import ugettext as _
from django.utils import timezone
from django.contrib.postgres.fields import ArrayField

from celery.task import Task
from celery.decorators import task
from celery.exceptions import Ignore
import vcf

from apps.authentication.models import User

from lib.utils import clogging
from lib.utils.io import count_file_lines
log = clogging.getColorLogger(__name__)


class Genome(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(default=timezone.now)

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
        return Genotype.objects.filter(genome_id=self.id)

    def delete_genotypes(self):
        self.get_genotypes().delete()

class Genotype(models.Model):
    genome = models.ForeignKey(Genome)
    rs_id_current = models.IntegerField()
    genotype = ArrayField(models.CharField(max_length=1024),size=2)


@task(ignore_result=True)
def task_import_genotypes(genome_id, minimum_snps=False):
    log.info('Importing genotypes ...')

    error = None

    try:
        genome = Genome.objects.get(id=uuid.UUID(genome_id))

        genotypes_found = genome.get_genotypes()
        if genotypes_found:
            log.info('Delete old records ...')
            genome.delete_genotypes()

        file_path = genome.get_genome_file()

        log.info('Converting to tsv ...')
        cmd = [os.path.join(settings.BASE_DIR, 'bin', 'vcf-to-tsv'),
               file_path,
               settings.RS_MERGE_ARCH_PATH,
               os.path.join(settings.BASE_DIR, 'bin')]
        subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()[0]

        log.info('Importing into database ...')
        genotypes = []
        with open(os.path.join(file_path + '.tsv'), 'rb') as fin:
            for i,line in enumerate(fin):
                record = line.strip().split('\t')
                genotype = record[1].split('/')
                genotypes.append(Genotype(genome=genome,
                                          rs_id_current=int(record[0]),
                                          genotype=genotype))

            Genotype.objects.bulk_create(genotypes)

    except Exception, exception:
        log.error('Unexpected error:' + str(exception))
        erorr = _('Invalid genome file.')

    finally:
        genome.status = 100
        genome.error = error

        if error:
            genome.status = -1
            genome.delete_genotypes()

        genome.save()

    log.info('Done!')
