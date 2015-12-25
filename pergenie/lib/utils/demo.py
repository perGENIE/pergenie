import os
import re
import shutil
import subprocess
from uuid import uuid4
from datetime import timedelta

from django.utils import timezone
from django.conf import settings

from apps.authentication.models import User, UserGrade
from apps.genome.models import Genome, Genotype
from apps.gwascatalog.models import GwasCatalogSnp
from apps.riskreport.models import RiskReport
from lib.utils.population import POPULATION_UNKNOWN, POPULATION_EAST_ASIAN
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

    # Init default demo genome (once)
    genome, is_created = Genome.objects.get_or_create(owner=admin_user,
                                                      file_name=settings.DEMO_GENOME_FILE_NAME,
                                                      display_name='Demo VCF',
                                                      file_format=Genome.FILE_FORMAT_VCF,
                                                      population=POPULATION_EAST_ASIAN,
                                                      gender=Genome.GENDER_MALE)
    # Init default demo genotype and riskreport (once)
    if is_created:
        # Prepare genome file
        genome_file_dir = os.path.join(settings.GENOME_UPLOAD_DIR, str(admin_user.id))
        if not os.path.exists(genome_file_dir):
            os.makedirs(genome_file_dir)
        genome_file_path = genome.get_genome_file()
        shutil.copyfile(src=os.path.join(settings.DEMO_GENOME_FILE_DIR, settings.DEMO_GENOME_FILE_NAME), dst=genome_file_path)

        genome.create_genotypes(async=False)
        log.info('Genotype created. count: {}'.format(Genotype.objects.filter(genome_id=genome.id).count()))

        # TODO: To update riskreport for new users, create risk report as async = True?
        riskreport = RiskReport.objects.create(genome=genome)
        riskreport.create_riskreport(async=False)
        log.info('RiskReport created. id: {}'.format(riskreport.id))

    # Init new demo user (everytime)
    email = '{}@{}'.format(uuid4(), settings.DOMAIN)
    demo_user = User.objects.create_user(username=email,
                                         email=email,
                                         password='',
                                         is_demo=True,
                                         grade=UserGrade(name='demo'))
    genome.readers.add(demo_user)
    log.info('User created. id: {}'.format(demo_user.id))

    log.info('Done')

    return demo_user


def prune_demo_user():
    """Prune old (not logged in 30 days) demo user records.
    """

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
