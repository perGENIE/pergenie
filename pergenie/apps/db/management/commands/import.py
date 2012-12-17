# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.conf import settings

from optparse import make_option
import sys
import os
import datetime

from termcolor import colored

import mongo.get_catalog as get_catalog
import mongo.clean_catalog as clean_catalog
import mongo.import_catalog as import_catalog

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option(
            "--gwascatalog",
            action="store_true",
            dest="gwascatalog",
            help=colored("Import GWAS Catalog into database", "green")
        ),
    )

    def handle(self, *args, **options):
        if options["gwascatalog"]:
            self.stdout.write('[INFO] Try to import latest gwascatalog...\n')

            # check if gwascatalog.<today>.txt is exists
            d = datetime.datetime.today()
            today = '{0}_{1}_{2}'.format(d.year, d.month, d.day)
            latest_catalog = os.path.join('data', 'gwascatalog.' + today + '.txt')
            if os.path.exists(latest_catalog):
                self.stdout.write('[INFO] Latest gwascatalog exists.\n')

            else:
                # get latest gwascatalog from official web site
                self.stdout.write('[INFO] Getting latest gwascatalog form official web site...\n')
                get_catalog.get_catalog(url=settings.GWASCATALOG_URL, dst=latest_catalog)
                
            # do `clean_catalog`
            self.stdout.write('[INFO] Cleaning latest gwascatalog...\n')
            clean_catalog.clean_catalog(latest_catalog, latest_catalog.replace('.txt', '.cleaned.txt'))
            

            # TODO: do `import_catalog`. collection name: [catalog][<today>]

            # TODO: do test_gatalog

            # TODO: update 'latest' catalog in db.catalog_info
            

        else:
            self.print_help("import", "help")
