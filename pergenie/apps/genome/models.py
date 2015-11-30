import os
import uuid
import subprocess

from django.db import models
from django.conf import settings
from django.utils.translation import ugettext as _
from django.utils import timezone
from django.contrib.postgres.fields import ArrayField
from celery.decorators import task

from apps.authentication.models import User
from apps.gwascatalog.models import GwasCatalogSnp
from lib.utils.population import POPULATION_CHOICES, POPULATION_UNKNOWN
from lib.utils import clogging
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
        return os.path.join(settings.GENOME_UPLOAD_DIR, str(self.owner.id), str(self.id))

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

    try:
        genome = Genome.objects.get(id=uuid.UUID(genome_id))

        genotypes_found = genome.get_genotypes()
        if genotypes_found:
            log.info('Delete old records ...')
            genome.delete_genotypes()

        file_path = genome.get_genome_file()

        log.info('Getting SNP ID whitelist ...')
        snp_id_whitelist = []
        snp_id_whitelist += GwasCatalogSnp.objects.exclude(snp_id_current__isnull=True).distinct('snp_id_current').values_list('snp_id_current', flat=True)
        with open(file_path + '.whitelist.txt', 'w') as fout:
            for snp_id in snp_id_whitelist:
                print >>fout, 'rs{}'.format(snp_id)

        log.info('Converting to tsv ...')
        cmd = [os.path.join(settings.BASE_DIR, 'bin', 'vcf-to-tsv'),
               file_path,
               settings.RS_MERGE_ARCH_PATH,
               os.path.join(settings.BASE_DIR, 'bin')]
        log.debug(cmd)
        subprocess.check_output(cmd)

        log.info('Importing into database ...')

        genotypes = []
        with open(file_path + '.tsv', 'r') as fin:
            for i,line in enumerate(fin):
                record = line.strip().split('\t')
                genotype = record[1].split('/')
                genotypes.append(Genotype(genome=genome,
                                          rs_id_current=int(record[0]),
                                          genotype=genotype))

            Genotype.objects.bulk_create(genotypes)
        genome.status = 100

    except Exception, exception:
        log.error('Unexpected error: ' + str(exception))
        genome.error = _('Invalid genome file.')
        genome.status = -1
        genome.delete_genotypes()

    finally:
        genome.save()

    log.info('Done!')
