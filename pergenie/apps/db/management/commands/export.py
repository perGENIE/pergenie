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
from lib.utils import clogging
log = clogging.getColorLogger(__name__)


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option(
            "--gwascatalog",
            action='store_true',
            help=""
        ),
    )

    def handle(self, *args, **options):
        if options["gwascatalog"]:
            log.info('Try to export gwascatalog...')
            gwascatalog.export_gwascatalog()

        else:
            self.print_help("export", "help")
