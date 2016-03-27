from uuid import uuid4

from django.core.management.base import BaseCommand, CommandError

from lib.utils.demo import create_or_update_demo_data
from lib.utils import clogging
log = clogging.getColorLogger(__name__)


class Command(BaseCommand):
    help = "Update demo data"

    def handle(self, *args, **options):
        create_or_update_demo_data(do_update=True)
