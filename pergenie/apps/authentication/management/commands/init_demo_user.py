from django.core.management.base import BaseCommand, CommandError
from django.db import models, transaction

from lib.utils import clogging
log = clogging.getColorLogger(__name__)


class Command(BaseCommand):
    help = "Initialize demo user"

    @transaction.atomic
    def handle(self, *args, **options):
        log.info('Not implimented yet')
