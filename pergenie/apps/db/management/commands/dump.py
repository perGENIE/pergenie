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
            mongo_auth_settings = []
            if settings.MONGO_PASSWORD:
                mongo_auth_settings = ['--username', settings.MONGO_USER,
                                       '--password', settings.MONGO_PASSWORD]

            print subprocess.Popen(['mongodump',
                                    '-h', str(settings.MONGO_HOST), '--port', str(settings.MONGO_PORT)]
                                   + mongo_auth_settings
                                   + ['--out', os.path.join(settings.BACKUP_DIR, 'mongo.dump.%s' % NOW)],
                                   stdout=subprocess.PIPE).communicate()[0]

        elif options["mysql"]:
            log.info('Dump MySQL backup...')

            # Add optional settings if exists
            mysql_optional_settings = []
            if settings.DATABASES['default']['HOST']:
                mysql_optional_settings.append('--host=%s' % settings.DATABASES['default']['HOST'])
            if settings.DATABASES['default']['PORT']:
                mysql_optional_settings.append('--port=%s' % settings.DATABASES['default']['PORT'])

            with open(os.path.join(settings.BACKUP_DIR, 'mysql.dump.%s.sql' % NOW), 'w') as fout:
                subprocess.Popen(['mysqldump',
                                  '--user=%s' % settings.DATABASES['default']['USER'],
                                  '--password=%s' % settings.DATABASES['default']['PASSWORD']]
                                 + mysql_optional_settings
                                 + ['pergenie'],
                                 stdout=fout)

        else:
            self.print_help("import", "help")
