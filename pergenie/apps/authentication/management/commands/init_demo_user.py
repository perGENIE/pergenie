from uuid import uuid4

from django.core.management.base import BaseCommand, CommandError

from lib.utils.demo import create_demo_user
from lib.utils import clogging
log = clogging.getColorLogger(__name__)


class Command(BaseCommand):
    help = "Initialize demo user"

    def handle(self, *args, **options):
        demo_user = create_demo_user()
        log.debug('id: {}'.format(demo_user.id))
        log.debug('email: {}'.format(demo_user.email))
