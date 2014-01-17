# -*- coding: utf-8 -*-

import sys, os
import glob
import shutil
from pprint import pprint
from optparse import make_option

from pymongo import MongoClient
from django.core.management.base import BaseCommand
from django.conf import settings
from lib.api.gwascatalog import GWASCatalog
gwascatalog = GWASCatalog()
from lib.mysql.hgmd import HGMD
from lib.utils import clogging
log = clogging.getColorLogger(__name__)


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option(
            "--gwascatalog",
            action='store_true',
            help=""
        ),
        make_option(
            "--hgmd",
            action='store_true',
            help=""
        ),
    )

    def handle(self, *args, **options):
        if options["gwascatalog"]:
            log.info('Try to export gwascatalog...')
            gwascatalog.export_gwascatalog()

        elif options["hgmd"]:
            log.info('Try to export HGMD...')

            hgmd = HGMD(settings.DATABASES['hgmd']['HOST'],
                        settings.DATABASES['hgmd']['USER'],
                        settings.DATABASES['hgmd']['PASSWORD'],
                        settings.DATABASES['hgmd']['NAME'],
                        settings.DATABASES['hgmd']['PORT'])

            #
            allmut = hgmd._allmut()
            print allmut

        else:
            self.print_help("export", "help")
