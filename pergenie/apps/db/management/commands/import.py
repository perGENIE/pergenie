# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.conf import settings

from optparse import make_option
import sys
import os
import datetime
import urllib
import pymongo
from termcolor import colored

from utils.date import today_date, today_str
from utils import clogging
log = clogging.getColorLogger(__name__)

import mongo.get_catalog as get_catalog
import mongo.clean_catalog as clean_catalog
import mongo.import_catalog as import_catalog

def get_catalog(url, dst):
    """Get latest gwascatalog.txt from NHGRI's web site."""
    
    # if not url:
    #     url = 'http://www.genome.gov/admin/gwascatalog.txt'

    log.info('Getting from {} ...'.format(url))
    
    # TODO: error handling
    urllib.urlretrieve(url, dst)


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option(
            "--gwascatalog",
            action="store_true",
            dest="gwascatalog",
            help=colored("Import GWAS Catalog into database", "green")
        ),
        # make_option(
        #     "-f",
        #     action="store_true",
        #     dest="force",
        #     help=colored("force", "green")
        # ),
    )

    def handle(self, *args, **options):
        if options["gwascatalog"]:
            log.info('Try to import latest gwascatalog...')

            # check if gwascatalog.<today>.txt is exists
            latest_catalog = os.path.join('data', 'gwascatalog.' + today_str + '.txt')

            if os.path.exists(latest_catalog):
                log.info('Latest gwascatalog exists.')
            else:
                # get latest gwascatalog from official web site
                log.info('Getting latest gwascatalog form official web site...')
                get_catalog.get_catalog(url=settings.GWASCATALOG_URL, dst=latest_catalog)
            

            latest_catalog_cleaned = latest_catalog.replace('.txt', '.cleaned.txt')

            if os.path.exists(latest_catalog_cleaned):
                log.info('Latest gwascatalog.cleaned exists.')
            else:
                # do `clean_catalog`
                log.info('Cleaning latest gwascatalog...')
                clean_catalog.clean_catalog(latest_catalog, latest_catalog_cleaned)
                

            # TODO: import latest gwascatalog as db.catalog.<today>
            import_catalog.import_catalog(path_to_gwascatalog=latest_catalog_cleaned,
                                          path_to_mim2gene=settings.PATH_TO_MIM2GENE,
                                          mongo_port=settings.MONGO_PORT)

            # TODO: do test_gatalog for db.catalog.<today>
                # TODO: check if latestet `date added` is newer or equal to prev's one. (check if download was succeed)
                # TODO: do risk report as test. (check if import catalog was succeed & odd records were handeled)

            # update 'latest' catalog in db.catalog_info
            with pymongo.Connection(port=settings.MONGO_PORT) as connection:
                log.info('MongoDB port: {}'.format(settings.MONGO_PORT))
                catalog_info = connection['pergenie']['catalog_info']

                latest_document = catalog_info.find_one({'status': 'latest'})

                log.info('latest_document: {}'.format(latest_document))
                log.info('today_date: {}'.format(today_date))

                if latest_document:
                    latest_date = latest_document['date']

                else:
                    # no latest, so today_date is latest
                    latest_date = today_date
                    catalog_info.update({'status': 'latest'}, {'$set': {'date': latest_date}}, upsert=True)
                    log.info('first time to  import catalog!')
                    log.info('today_date: {}'.format(today_date))

                # check if today_date is newer than latest
                if today_date > latest_date:
                    # update latest
                    prev_date = latest_date
                    catalog_info.update({'status': 'latest'}, {'$set': {'date': latest_date}}, upsert=True)
                    catalog_info.update({'status': 'prev'}, {'$set': {'date': prev_date}}, upsert=True)
                    log.info('updated latest in db.catalog_info')
                    log.info('today_date: {}'.format(today_date))

                else:
                    # do not update
                    pass

        else:
            self.print_help("import", "help")
