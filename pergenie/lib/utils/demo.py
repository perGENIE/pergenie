from uuid import uuid4
from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import models, transaction
from django.utils import timezone
from django.conf import settings

from apps.authentication.models import User
from apps.genome.models import Genome
from lib.utils import clogging
log = clogging.getColorLogger(__name__)


# TODO: @transaction.atomic
def create_demo_user():
    '''Create demo user records.

    - demo Genome is defined as:
      - owner = one of the admin users
      - file_name = settings.DEMO_GENOME_FILE_NAME

    - demo User is defined as:
      - is_demo = True
    '''

    admin_user = User.objects.filter(is_admin=True).last()
    if not admin_user:
        raise Exception, '[FATAL] Before create demo user, you need to create admin user: $ python manage.py createsuperuser'

    # Init demo genome (once)
    genome, is_created = Genome.objects.get_or_create(owner=admin_user,
                                                      file_name=settings.DEMO_GENOME_FILE_NAME,
                                                      display_name='Demo VCF',
                                                      file_format=Genome.FILE_FORMAT_VCF,
                                                      population=Genome.POPULATION_UNKNOWN,
                                                      sex=Genome.SEX_UNKNOWN)

    # TODO: Init demo genotype (once)

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
