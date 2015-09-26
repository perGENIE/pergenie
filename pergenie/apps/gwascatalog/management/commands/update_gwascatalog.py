import sys
import os
import re
import glob
import datetime

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from apps.gwascatalog.models import GWASCatalog
from lib.utils.io import get_url_content
from lib.utils import clogging
log = clogging.getColorLogger(__name__)


class Command(BaseCommand):
    help = "Update GWAS Catalog"

    def handle(self, *args, **options):
        try:
            log.info('Fetching latest gwascatalog...')

            catalog_dir = os.path.join(settings.UPLOAD_DIR, 'gwascatalog')
            if not os.path.exists(catalog_dir):
                os.makedirs(catalog_dir)

            catalog_path = os.path.join(catalog_dir, 'gwascatalog.{}.txt'.format(datetime.datetime.now().strftime('%Y%m%d')))
            log.debug(catalog_path)

            if not os.path.exists(catalog_path):
                try:
                    get_url_content(url=settings.GWASCATALOG_URL, dst=catalog_path)
                except (IOError,KeyboardInterrupt) as exception:
                    if os.path.exists(catalog_path):
                        os.remove(catalog_path)
                    raise

            log.info('Importing gwascatalog...')

            # TODO: parse dbsnp-pg-min/contrib/gwascatalog

            # TODO: cleanup records
            # _calc_reliability_rank()
            # _population()
            # OR/beta
            # _platform()
            # _risk_allele()

            # TODO: create GwasCatalog models

            # TODO: activation

            log.info('Done.')

        except Exception as exception:
            # TODO: rollback
            # catalog.delete_catalog()
            # catalog.delete()
            raise
