# -*- coding: utf-8 -*-

import sys, os
import glob
import datetime
import subprocess
from optparse import make_option
from termcolor import colored
from django.core.management.base import BaseCommand
from django.conf import settings

from lib.utils.date import today_str
from lib.utils import clogging
log = clogging.getColorLogger(__name__)

MINDATE = datetime.datetime(1989, 1, 1, 0, 0)
NOW = today_str


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option(
            "--mongo",
            action="store_true",
            dest="mongo",
            help=colored("Restore MongoDB backup", "green")
        ),
        make_option(
            "--mysql",
            action="store_true",
            dest="mysql",
            help=colored("Restore MySQL backup", "green")
        ),
    )

    def handle(self, *args, **options):
        if options["mongo"]:
            log.info('Restore MongoDB backup...')

            # Get latest backup by checking timestamp
            backups = glob.glob(os.path.join(settings.BASE_DIR, 'mongo.dump.*'))
            latest_backup = ''
            latest_backup_timestamp = MINDATE
            for backup in backups:
                last_modified = datetime.datetime.fromtimestamp(os.path.getmtime(backup))
                if latest_backup_timestamp < last_modified:
                    latest_backup_timestamp = last_modified
                    latest_backup = backup

            log.info('latest_backup: %s' % latest_backup)
            log.info('Proceed restore?')
            yn = raw_input('y/n > ')
            if yn == 'y':
                # Add auth settings if exists
                if settings.MONGO_PASSWORD:
                    mongo_auth_settings = ['--username', settings.MONGO_USER,
                                           '--password', settings.MONGO_PASSWORD]
                else:
                    mongo_auth_settings = []

                print subprocess.Popen(['mongorestore',
                                        '-h', str(settings.MONGO_HOST), '--port', str(settings.MONGO_PORT)]
                                       + mongo_auth_settings
                                       + ['--drop', latest_backup],
                                       stdout=subprocess.PIPE).communicate()[0]
            else:
                sys.exit()


        elif options["mysql"]:
            log.info('Restore MySQL backup...')

            latest_backup = 'pergenie.dump.***.sql'
            log.info('latest_backup: %s' % latest_backup)
            log.info('Proceed restore?')
            yn = raw_input('y/n > ')
            if yn == 'y':
                pass

                # TODO:
                # print subprocess.Popen(['mysql',
                #                         '--user=%s' % settings.DATABASES['default']['USER'],
                #                         '--password=%s' % settings.DATABASES['default']['PASSWORD'],
                #                         'pergenie', '<', latest_backup],
                #                        stdout=subprocess.PIPE).communicate()[0]
            else:
                sys.exit()

        else:
            self.print_help("import", "help")
