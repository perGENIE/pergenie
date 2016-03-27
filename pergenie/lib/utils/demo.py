import os
import re
import shutil
import subprocess
from uuid import uuid4
from datetime import timedelta

from django.db import IntegrityError, transaction
from django.utils import timezone
from django.conf import settings

from apps.authentication.models import User, UserGrade
from apps.genome.models import Genome, Genotype
from apps.gwascatalog.models import GwasCatalogSnp
from apps.riskreport.models import RiskReport
from apps.population.models import PopulationPcaGeoPoint
from lib.utils.population import POPULATION_UNKNOWN, POPULATION_EAST_ASIAN
from lib.utils import clogging
log = clogging.getColorLogger(__name__)


def create_demo_user():
    """Create demo user records.

    - demo Genome is defined as:
      - owner == one of the admin users
      - file_name == settings.DEMO_GENOME_FILE_NAME

    - demo User is defined as:
      - grade.name == 'demo'
    """

    genome = create_or_update_demo_data()

    # Init new demo user (everytime)
    email = '{}@{}'.format(uuid4(), settings.DOMAIN)
    demo_user_grade, _ = UserGrade.objects.get_or_create(name='demo')
    demo_user = User.objects.create_user(username=email,
                                         email=email,
                                         password='',
                                         grade=demo_user_grade)
    genome.readers.add(demo_user)
    log.info('User created. id: {}'.format(demo_user.id))

    log.info('Done')

    return demo_user

def create_or_update_demo_data(do_update=False):
    """Create or update demo data.

    By default, demo data is created only once when demo user is created.
    If `do_update` is True, demo data will be force updated.
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
    if is_created or do_update:
        # Prepare genome file
        genome_file_dir = os.path.join(settings.GENOME_UPLOAD_DIR, str(admin_user.id))
        if not os.path.exists(genome_file_dir):
            os.makedirs(genome_file_dir)
        genome_file_path = genome.get_genome_file()
        shutil.copyfile(src=os.path.join(settings.DEMO_GENOME_FILE_DIR, settings.DEMO_GENOME_FILE_NAME), dst=genome_file_path)

        genome.create_genotypes(async=False)
        log.info('Genotype created. count: {}'.format(Genotype.objects.filter(genome_id=genome.id).count()))

        # RiskReport
        # TODO: need refactoring
        while True:
            try:
                with transaction.atomic():
                    #
                    demo_risk_reports = RiskReport.objects.filter(genome=genome)
                    if demo_risk_reports:
                        log.info('Delete old records: RiskReport ...')
                        demo_risk_reports.delete()

                    #
                    riskreport = RiskReport.objects.create(genome=genome, display_id=User.objects.make_random_password(8))
                    break
            except IntegrityError:
                log.warn('IntegrityError with RiskReport.objects.create')

        # TODO: To update riskreport for new users, create risk report as async = True?
        riskreport.create_riskreport(async=False)
        log.info('RiskReport created. id: {}'.format(riskreport.id))

        # PopulationPcaGeoPoint
        with transaction.atomic():
            demo_geo_point = PopulationPcaGeoPoint.objects.filter(genome=genome)
            if demo_geo_point:
                log.info('Delete old records: PopulationPcaGeoPoint ...')
                demo_geo_point.delete()

            geo_point = PopulationPcaGeoPoint.objects.create(genome=genome, population_code='global')
            geo_point.create_geo_point(async=False)
            log.info('Population PCA Geo Point created. id: {}'.format(geo_point.id))

    return genome

def prune_demo_user():
    """Prune old (not logged in 30 days) demo user records.
    """

    date_30_days_ago = timezone.now() - timedelta(30)
    not_logged_in_30_days_demo_users = User.objects.filter(grade__name='demo', last_login__lt=date_30_days_ago)

    admin_users = User.objects.filter(is_admin=True)
    demo_genomes = Genome.objects.filter(owner__in=admin_users, file_name=settings.DEMO_GENOME_FILE_NAME)
    for genome in demo_genomes:
        for user in not_logged_in_30_days_demo_users:
            if user in genome.readers.all():
                genome.readers.remove(user)

    not_logged_in_30_days_demo_users.delete()

class CreateDemoUserError(Exception): pass
