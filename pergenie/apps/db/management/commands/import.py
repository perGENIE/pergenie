# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.conf import settings

from optparse import make_option
import sys
import os
import datetime

from termcolor import colored
import pymongo

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
        make_option(
            "-f",
            action="store_true",
            dest="force",
            help=colored("force", "green")
        ),
    )

    def handle(self, *args, **options):
        if options["gwascatalog"]:
            self.stdout.write('[INFO] Try to import latest gwascatalog...\n')
            self.stdout.write('[INFO] Force {}\n'.format(options['force']))

            # check if gwascatalog.<today>.txt is exists
            d = datetime.datetime.today()
            today = '{0}_{1}_{2}'.format(d.year, d.month, d.day)
            latest_catalog = os.path.join('data', 'gwascatalog.' + today + '.txt')

            if os.path.exists(latest_catalog) and not options['force']:
                self.stdout.write('[INFO] Latest gwascatalog exists.\n')
            else:
                # get latest gwascatalog from official web site
                self.stdout.write('[INFO] Getting latest gwascatalog form official web site...\n')
                get_catalog.get_catalog(url=settings.GWASCATALOG_URL, dst=latest_catalog)
            
            latest_catalog_cleaned = latest_catalog.replace('.txt', '.cleaned.txt')

            if os.path.exists(latest_catalog_cleaned) and not options['force']:
                self.stdout.write('[INFO] Latest gwascatalog.cleaned exists.\n')
            else:
                # do `clean_catalog`
                self.stdout.write('[INFO] Cleaning latest gwascatalog...\n')
                clean_catalog.clean_catalog(latest_catalog, latest_catalog_cleaned)
                
            # TODO: import latest gwascatalog as db.catalog.<today>
            import_catalog.import_catalog(path_to_gwascatalog=latest_catalog_cleaned,
                                          path_to_mim2gene=os.path.join('data', 'mim2gene.txt'),
                                          path_to_pickled_catalog=None,
                                          mongo_port=settings.MONGO_PORT)


            # TODO: do test_gatalog for db.catalog.<today>

            # TODO: update 'latest' catalog in db.catalog_info
#             with pymongo.Connection(port=settings.MONGO_PORT) as connection:
#                 catalog_info = connection['pergenie']['catalog_info']

#                 catalog_info_document = catalog_info.find_one()
#                 if catalog_info_document:
#                     prev = catalog_info_document['latest']
#                 else:
#                     prev = None
#                 catalog_info.update({'latest': today}, )
                

        else:
            self.print_help("import", "help")
