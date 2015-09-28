import sys
import os
import csv
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.db import models, transaction
from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_date

from apps.gwascatalog.models import GwasCatalogSnp
from lib.utils.io import get_url_content
from lib.utils import clogging
log = clogging.getColorLogger(__name__)


class Command(BaseCommand):
    help = "Update GWAS Catalog"

    @transaction.atomic
    def handle(self, *args, **options):
        log.info('Fetching latest gwascatalog...')

        if not os.path.exists(settings.GWASCATALOG_DIR):
            os.makedirs(settings.GWASCATALOG_DIR)

        today = timezone.now().strftime('%Y-%m-%d')
        catalog_path = os.path.join(settings.GWASCATALOG_DIR, 'gwascatalog_cleaned_{}.tsv'.format(today))

        log.info('Importing gwascatalog...')

        chunk_length = 1000
        snps = []

        current_tz = timezone.get_current_timezone()
        log.info(current_tz)

        model_fields = [field for field in GwasCatalogSnp._meta.get_fields() if field.name not in ('id', 'created_at')]
        model_field_names = [field.name for field in model_fields]
        model_fields_map = dict(zip(model_field_names, model_fields))

        reader = csv.DictReader(open(catalog_path, 'rb'), delimiter='\t')
        for record in reader:
            # population = get_population(record['initial_sample_size'])

            # if population:
            #     population_1st = population[0]
            #     db_allele_freq = {'Asian': {}, 'European': {}, 'African': {}}[population_1st]  # TODO
            # else:
            #     db_allele_freq = {}

            # TODO: odds_ratio/beta_coeff

            record.update({'risk_allele_forward': '',
                           'population': [],
                           'reliability_rank': '',
                           'odds_ratio': None,
                           'beta_coeff': None})

            data = {}
            for k,v in record.items():
                if k in model_field_names:
                    # blank or null
                    if v == '':
                        if type(model_fields_map[k]) in (models.fields.CharField, models.fields.TextField):
                            v = ''
                        else:
                            v = None

                    # datetime with timezone
                    if type(model_fields_map[k]) == models.DateTimeField:
                        v = current_tz.localize(datetime(*(parse_date(v).timetuple()[:5])))

                    data[k] = v

            snps.append(GwasCatalogSnp(**data))

            if len(snps) == chunk_length:
                log.debug('processed: {} records'.format(len(snps)))
                GwasCatalogSnp.objects.bulk_create(snps)
                snps[:] = []

        if len(snps) > 0:
            log.debug('processed: {} records'.format(len(snps)))
            GwasCatalogSnp.objects.bulk_create(snps)

        log.info('Done.')
