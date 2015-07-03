# -*- coding: utf-8 -*-

import sys
import os
import re
import glob
import datetime
from optparse import make_option
from termcolor import colored
from pymongo import MongoClient

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from lib.mongo.clean_catalog import clean_catalog
from lib.mongo.import_catalog import import_catalog
from lib.utils.date import today_date, today_str
from lib.utils import clogging
log = clogging.getColorLogger(__name__)
from utils.io import get_url_content


def date2datetime(d):
    return datetime.datetime.combine(d, datetime.time())


class Command(BaseCommand):
    help = colored("Import GWAS Catalog into database", "green")


    def handle(self, *args, **options):
        log.info('Try to import latest gwascatalog...')

        # check if gwascatalog.<today>.txt is exists
        latest_catalog = os.path.join(settings.BASE_DIR, 'data', 'gwascatalog.' + today_str + '.txt')
        latest_date = today_date

        if os.path.exists(latest_catalog):
            log.info('Latest gwascatalog exists.')
        else:
            # get latest gwascatalog from official web site
            log.info('Getting latest gwascatalog form official web site...')
            log.info('Getting from {0} ...'.format(settings.GWASCATALOG_URL))

            try:
                get_url_content(url=settings.GWASCATALOG_URL, dst=latest_catalog)
                # download_file(url=settings.GWASCATALOG_URL, dst=latest_catalog)
            except IOError:
                log.error('Could not get latest gwascatalog.')
                log.error('Proceed importing gwascatalog with local gwascatalog? (may not latest)')
                yn = raw_input('y/n > ')

                if yn == 'y':
                    # get latest in local
                    re_datetime = re.compile('gwascatalog\.(\d+)_(\d+)_(\d+)\.txt')
                    local_latest_date = datetime.date(2000, 01, 01)
                    for c in glob.glob(os.path.join(settings.BASE_DIR, 'data', 'gwascatalog.*.txt')):
                        tmp_date = re_datetime.findall(c)
                        if tmp_date:
                            tmp_date = datetime.date(int(tmp_date[0][0]), int(tmp_date[0][1]), int(tmp_date[0][2]))
                            if tmp_date > local_latest_date:
                                local_latest_date = tmp_date

                    latest_catalog = os.path.join(settings.BASE_DIR, 'data', 'gwascatalog.' + str(local_latest_date).replace('-', '_') + '.txt')
                    latest_date = local_latest_date

                    log.warn('=======================================================')
                    log.warn('Use local latest gwascatalog: {0}'.format(latest_catalog))
                    log.warn('=======================================================')

                else:
                    log.info('Importing gwascatalog stopped.')
                    sys.exit()

        latest_catalog_cleaned = latest_catalog.replace('.txt', '.cleaned.txt')

        if os.path.exists(latest_catalog_cleaned):
            log.info('Latest gwascatalog.cleaned exists.')
        else:
            # do `clean_catalog`
            log.info('Cleaning latest gwascatalog...')
            clean_catalog(latest_catalog, latest_catalog_cleaned)

        import_catalog(latest_catalog_cleaned)

        # TODO: get latest information of gwascatalog (dbSNP version & refgenome version)
        # form .pdf -> x
        # from .html -> TODO


        # TODO: do test_gatalog for db.catalog.<today>
            # TODO: check if latestet `date added` is newer or equal to prev's one. (check if download was succeed)
            # TODO: do risk report as test. (check if import catalog was succeed & odd records were handeled)

        # update 'latest' catalog in db.catalog_info
        with MongoClient(host=settings.MONGO_URI) as c:
            catalog_info = c['pergenie']['catalog_info']

            latest_document = catalog_info.find_one({'status': 'latest'})
            log.info('latest_document: {0}'.format(latest_document))

            #
            latest_date = date2datetime(latest_date)

            if latest_document:
                db_latest_date = latest_document['date']

            else:
                # no latest in catalog_info
                db_latest_date = latest_date
                catalog_info.update({'status': 'latest'}, {'$set': {'date': db_latest_date}}, upsert=True)
                log.info('First time to import catalog!')

            # check if is newer than latest in catalog_info
            if latest_date > db_latest_date:
                # update latest
                catalog_info.update({'status': 'latest'}, {'$set': {'date': latest_date}}, upsert=True)
                catalog_info.update({'status': 'prev'}, {'$set': {'date': db_latest_date}}, upsert=True)
                log.info('Updated latest in catalog_info.')

            else:
                log.info('No need to update catalog_info.')

            log.info('latest: {0}'.format(catalog_info.find_one({'status': 'latest'})))
