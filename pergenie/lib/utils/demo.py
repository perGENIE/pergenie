from uuid import uuid4

from django.core.management.base import BaseCommand, CommandError
from django.db import models, transaction
from django.conf import settings

from apps.authentication.models import User
from apps.genome.models import Genome
from lib.utils import clogging
log = clogging.getColorLogger(__name__)


# TODO: @transaction.atomic
def create_demo_user():
    admin_user = User.objects.filter(is_admin=True).last()
    if not admin_user:
        raise Exception, '[FATAL] Before create demo user, you need to create admin user: $ python manage.py createsuperuser'

    # Init demo genome (once)
    genome, is_created = Genome.objects.get_or_create(owner=admin_user,
                                                      file_name='demo.vcf',
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
    # TODO: remove old demo users
    pass
