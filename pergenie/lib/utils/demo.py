import os
import shutil
import subprocess
from uuid import uuid4
from datetime import timedelta

from django.utils import timezone
from django.conf import settings

from apps.authentication.models import User
from apps.genome.models import Genome, Genotype
from apps.gwascatalog.models import GwasCatalogSnp
from apps.riskreport.models import RiskReport
from lib.utils import clogging
log = clogging.getColorLogger(__name__)


def create_demo_user():
    """Create demo user records.

    - demo Genome is defined as:
      - owner = one of the admin users
      - file_name = settings.DEMO_GENOME_FILE_NAME

    - demo User is defined as:
      - is_demo = True
    """

    admin_user = User.objects.filter(is_admin=True).last()
    if not admin_user:
        raise CreateDemoUserError('[FATAL] Before create demo user, you need to create admin user: $ python manage.py createsuperuser')

    # Init demo genome (once)
    genome, is_created = Genome.objects.get_or_create(owner=admin_user,
                                                      file_name=settings.DEMO_GENOME_FILE_NAME,
                                                      display_name='Demo VCF',
                                                      file_format=Genome.FILE_FORMAT_VCF,
                                                      population=Genome.POPULATION_UNKNOWN,
                                                      sex=Genome.SEX_UNKNOWN)
    # Init demo genotype (once)
    if is_created:
        # Prepare genome file
        genome_file_dir = os.path.join(settings.GENOME_UPLOAD_DIR, str(admin_user.id))
        if not os.path.exists(genome_file_dir):
            os.makedirs(genome_file_dir)
        genome_file_path = genome.get_genome_file()
        shutil.copyfile(src=os.path.join(settings.DEMO_GENOME_FILE_DIR, settings.DEMO_GENOME_FILE_NAME), dst=genome_file_path)

        # Create SNP whitelist
        snp_id_whitelist = GwasCatalogSnp.objects.exclude(snp_id_current__isnull=True).distinct().values_list('snp_id_current', flat=True)
        with open(genome_file_path + '.whitelist.txt', 'w') as fout:
            for snp_id in snp_id_whitelist:
                print >>fout, 'rs{}'.format(snp_id)

        # Cleanup genome file
        cmd = [os.path.join(settings.BASE_DIR, 'bin', 'vcf-to-tsv'),
               genome_file_path,
               settings.RS_MERGE_ARCH_PATH,
               os.path.join(settings.BASE_DIR, 'bin')]
        subprocess.check_output(cmd)

        log.info('Cleanup genome file: {}'.format(cmd))

        # Create genotype records
        genotypes = []
        with open(genome_file_path + '.tsv', 'r') as fin:
            for i,line in enumerate(fin):
                record = line.strip().split('\t')
                genotype = record[1].split('/')
                genotypes.append(Genotype(genome=genome,
                                          rs_id_current=int(record[0]),
                                          genotype=genotype))
            Genotype.objects.bulk_create(genotypes)

        log.info('Genotype created: {}'.format(Genotype.objects.filter(genome_id=genome.id).count()))

        genome.status = 100
        genome.save()

    # Create riskreport
    riskreport, _ = RiskReport.objects.get_or_create(genome=genome)
    log.info('RiskReport get_or_created id: {}'.format(riskreport.id))

    riskreport.create_riskreport()

    # Init demo user
    email = '{}@{}'.format(uuid4(), settings.DOMAIN)
    demo_user = User.objects.create_user(username=email,
                                         email=email,
                                         password='',
                                         is_demo=True)
    genome.readers.add(demo_user)

    return demo_user


def prune_demo_user():
    '''Prune old (not logged in 30 days) demo user records.
    '''

    date_30_days_ago = timezone.now() - timedelta(30)
    not_logged_in_30_days_demo_users = User.objects.filter(is_demo=True, last_login__lt=date_30_days_ago)

    admin_users = User.objects.filter(is_admin=True)
    demo_genomes = Genome.objects.filter(owner__in=admin_users, file_name=settings.DEMO_GENOME_FILE_NAME)
    for genome in demo_genomes:
        for user in not_logged_in_30_days_demo_users:
            if user in genome.readers.all():
                genome.readers.remove(user)

    not_logged_in_30_days_demo_users.delete()


class CreateDemoUserError(Exception): pass
