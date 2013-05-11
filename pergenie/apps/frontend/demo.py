from django.contrib.auth.models import User
from django.conf import settings


def create_demo_user():
    User.objects.create_user(settings.DEMO_USER_ID,
                             '',
                             settings.DEMO_USER_ID)

    _import_genome_files_for_demo()


def _import_genome_files_for_demo():
    # TODO: import tomita genome
    pass
