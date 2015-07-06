# -*- coding: utf-8 -*-

import sys
import os
import re
import glob
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from apps.gwascatalog.models import GWASCatalog
from ._clean import clean_catalog
from ._import import import_catalog

from lib.utils.io import get_url_content
from lib.utils import clogging
log = clogging.getColorLogger(__name__)


class Command(BaseCommand):
    help = "Import GWAS Catalog into database"

    def handle(self, *args, **options):
        log.info('Trying to import latest gwascatalog...')

        catalog = GWASCatalog()
        catalog.save()

        try:
            catalog_dir = os.path.join(settings.UPLOAD_DIR, 'gwascatalog')
            if not os.path.exists(catalog_dir):
                os.makedirs(catalog_dir)

            log.info('Getting latest gwascatalog form official web site...')
            catalog_path = os.path.join(catalog_dir, 'gwascatalog.{}.txt'.format(datetime.now().strftime('%Y%m%d-%H%M')))
            get_url_content(url=settings.GWASCATALOG_URL, dst=catalog_path)

            log.info('Cleaning gwascatalog...')
            catalog_cleaned_path = re.sub(r'\.txt$', '.cleaned.txt', catalog_path)
            clean_catalog(source=catalog_path, destination=catalog_cleaned_path)

            log.info('Importing gwascatalog...')
            import_catalog(source=catalog_cleaned_path, catalog_id=catalog.id)

            catalog.is_active = True
            catalog.save()

            log.info('Done.')

        except Exception as exception:
            log.error(exception)
            # TODO: delete mongodb collection
            catalog.delete()
