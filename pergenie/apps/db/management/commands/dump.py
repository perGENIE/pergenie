# -*- coding: utf-8 -*-

import sys, os
import subprocess
from optparse import make_option
from termcolor import colored
from django.core.management.base import BaseCommand
from django.conf import settings

from lib.utils.date import today_str
from lib.utils import clogging
log = clogging.getColorLogger(__name__)


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option(
            "--mongo",
            action="store_true",
            dest="mongo",
            help=colored("Dump MongoDB backup", "green")
        ),
        make_option(
            "--mysql",
            action="store_true",
            dest="mysql",
            help=colored("Dump MySQL backup", "green")
        ),
    )

    def handle(self, *args, **options):
        NOW = today_str
        if options["mongo"]:
            # 1台なのでdump&restoreでやる。(shardingしていればファイルコピーでよい)
            log.info('Dump MongoDB backup...')

            # Add auth settings if exists
            if settings.MONGO_PASSWORD:
                mongo_auth_settings = ['--username', settings.MONGO_USER,
                                       '--password', settings.MONGO_PASSWORD]
            else:
                mongo_auth_settings = []

            print subprocess.Popen(['mongodump',
                                    '-h', str(settings.MONGO_HOST), '--port', str(settings.MONGO_PORT)]
                                   + mongo_auth_settings
                                   + ['--out', os.path.join(settings.BACKUP_DIR, 'mongo.dump.%s' % NOW)],
                                   stdout=subprocess.PIPE).communicate()[0]

        elif options["mysql"]:
            log.info('Dump MySQL backup...')

            # TODO: add auth settings
            print subprocess.Popen(['mysqldump',
                                    '--user=%s' % settings.DATABASES['default']['USER'],
                                    '--password=%s' % settings.DATABASES['default']['PASSWORD'],
                                    'pergenie'],
                                   stdout=subprocess.PIPE).communicate()[0]

        else:
            self.print_help("import", "help")
