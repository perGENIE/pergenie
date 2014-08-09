# -*- coding: utf-8 -*-

import sys, os
import re
import glob
import datetime
import subprocess
from optparse import make_option
from termcolor import colored
from pymongo import MongoClient
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings

from lib.mysql.import_bioq import import_bioq
from lib.mongo.import_refFlat import import_refFlat
from lib.mongo.import_OMIM import OMIMParser
from lib.mongo.clean_catalog import clean_catalog
from lib.mongo.import_catalog import import_catalog
from lib.mongo.import_population_pca import import_population_pca
from lib.mongo.import_genomes import import_genomes
from lib.mongo.import_mycatalog import import_mycatalog
# from lib.mongo.import_snp_freq import import_snp_freq

from lib.common import clean_file_name
from lib.mongo.import_variants import import_variants
from lib.utils.date import today_date, today_str
from lib.utils import clogging
log = clogging.getColorLogger(__name__)
from utils.io import get_url_content


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
        make_option(
            "--demodata",
            action="store_true",
            dest="demodata",
            help=colored("Import Demo data & Demo user (if not exists) into database", "green")
        ),
        make_option(
            "--bioq",
            action="store_true",
            dest="bioq",
            help=colored("Import BioQ into database", "green")
        ),
        make_option(
            "--pdb",
            action="store_true",
            dest="pdb",
            help=colored("Import PDB", "green")
        ),
        make_option(
            "--refflat",
            action="store_true",
            dest="refflat",
            help=colored("Import refFlat into database", "green")
        ),
        make_option(
            "--omim",
            action="store_true",
            dest="omim",
            help=colored("Import OMIM into database", "green")
        ),
        make_option(
            "--population_pca",
            action="store_true",
            dest="population_pca",
            help=colored("Import Population PCA data into database", "green")
        ),
        make_option(
            "--genomes",
            action="store_true",
            dest="genomes",
            help=colored("Import genome data (to be used as cron job)", "green")
        ),
        make_option(
            "--mycatalog",
            dest="mycatalog",
            help=colored("Import my catalog into database", "green")
        ),
        make_option(
            "--snp-freq",
            action="store_true",
            # dest="snp_freq",
            help=colored("Import SNP frequency data into database", "green")
        ),
    )

    def handle(self, *args, **options):
        if options["gwascatalog"]:
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


        elif options["demodata"]:
            # Create user
            if not User.objects.filter(username=settings.DEMO_USER_ID):
                User.objects.create_user(settings.DEMO_USER_ID,
                                         '',
                                         settings.DEMO_USER_ID)

                # no need to make directory for upload, because we will import from *stored data*.

                # create user_info
                with MongoClient(host=settings.MONGO_URI) as c:
                    user_info = c['pergenie']['user_info']

                    if user_info.find_one({'user_id': settings.DEMO_USER_ID}):
                        user_info.remove({'user_id': settings.DEMO_USER_ID})

                    user_info.insert({'user_id': settings.DEMO_USER_ID,
                                      'risk_report_show_level': 'show_all',
                                      'activation_key': ''})

            #
            import_genomes(settings, user_ids=[settings.DEMO_USER_ID])

        elif options["bioq"]:
            log.info('Try to import bioq ...')
            import_bioq(settings)
        elif options["pdb"]:
            p0 = subprocess.Popen(['rsync', '-avz', '--delete', 'ftp.pdbj.org::ftp_data/structures/divided/pdb/', settings.PATH_TO_PDB])
            log.info(p0.communicate()[0])
        elif options["refflat"]:
            log.info('Try to import refflat ...')
            import_refFlat(settings)
        elif options["omim"]:
            log.info('Try to import omim ...')
            omim_parser = OMIMParser(settings)
            omim_parser.insert_to_mongo()
            omim_parser.check()
        elif options["population_pca"]:
            log.info('Try to import population_pca ...')
            import_population_pca(settings)
        elif options["genomes"]:
            # log.info('Try to import genomes (genome data) ...')

            # pidfile_path = os.path.join(settings.BASE_DIR, 'import_genomes.pid')
            # if os.path.exists(pidfile_path):
            #     log.error('Previous process has not finished yet.')
            #     sys.exit()

            # with open(pidfile_path, 'w') as pidfile:
            #     print >>pidfile, os.getpid()

            import_genomes(settings)
            # os.remove(pidfile_path)
        elif options["mycatalog"]:
            log.info('Try to import mycatalog ...')
            import_mycatalog(options["mycatalog"])
        elif options["snp_freq"]:
            log.info('Try to import snp_freq ...')
            import_snp_freq()

        else:
            self.print_help("import", "help")
