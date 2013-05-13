# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.conf import settings

from optparse import make_option
import sys
import os
import re
import datetime
import pymongo
from termcolor import colored
import glob

from utils.date import today_date, today_str
from utils import clogging
log = clogging.getColorLogger(__name__)
from utils.io import get_url_content

import mongo.clean_catalog as clean_catalog
import mongo.import_catalog as import_catalog


def date2datetime(d):
    return datetime.datetime.combine(d, datetime.time())


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
            latest_date = today_date

            if os.path.exists(latest_catalog):
                log.info('Latest gwascatalog exists.')
            else:
                # get latest gwascatalog from official web site
                log.info('Getting latest gwascatalog form official web site...')
                log.info('Getting from {} ...'.format(settings.GWASCATALOG_URL))

                try:
                    get_url_content(url=settings.GWASCATALOG_URL, dst=latest_catalog)
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

                        latest_catalog = os.path.join('data', 'gwascatalog.' + str(local_latest_date).replace('-', '_') + '.txt')
                        latest_date = local_latest_date

                        log.warn('=======================================================')
                        log.warn('Use local latest gwascatalog: {}'.format(latest_catalog))
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
                clean_catalog.clean_catalog(latest_catalog, latest_catalog_cleaned)

            import_catalog.import_catalog(path_to_gwascatalog=latest_catalog_cleaned,
                                          path_to_mim2gene=settings.PATH_TO_MIM2GENE,
                                          path_to_eng2ja=settings.PATH_TO_ENG2JA,
                                          path_to_disease2wiki=settings.PATH_TO_DISEASE2WIKI,
                                          path_to_interval_list_dir=settings.PATH_TO_INTERVAL_LIST_DIR,
                                          path_to_reference_fasta=settings.PATH_TO_REFERENCE_FASTA,
                                          catalog_summary_cache_dir=settings.CATALOG_SUMMARY_CACHE_DIR,
                                          mongo_port=settings.MONGO_PORT)

            # TODO: get latest information of gwascatalog (dbSNP version & refgenome version)
            # form .pdf -> x
            # from .html -> TODO


            # TODO: do test_gatalog for db.catalog.<today>
                # TODO: check if latestet `date added` is newer or equal to prev's one. (check if download was succeed)
                # TODO: do risk report as test. (check if import catalog was succeed & odd records were handeled)

            # update 'latest' catalog in db.catalog_info
            with pymongo.Connection(port=settings.MONGO_PORT) as connection:
                catalog_info = connection['pergenie']['catalog_info']

                latest_document = catalog_info.find_one({'status': 'latest'})
                log.info('latest_document: {}'.format(latest_document))

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

                log.info('latest: {}'.format(catalog_info.find_one({'status': 'latest'})))

        else:
            self.print_help("import", "help")
