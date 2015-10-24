import sys
import os
import csv
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.db import models, transaction
from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_date

from apps.snp.models import Snp
from apps.gwascatalog.models import GwasCatalogSnp, GwasCatalogPhenotype
from cleanup.population import get_population
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

        # TODO: Fetch from web
        current_tz = timezone.get_current_timezone()
        # today = timezone.now().strftime('%Y-%m-%d')
        today = timezone.now().strftime('2015-09-25')  # FIXME
        today_with_tz = current_tz.localize(datetime(*(parse_date(today).timetuple()[:5])))

        # - Allele freq
        log.info('Updating snp allele freq records for gwascatalog...')
        catalog_freq_path = os.path.join(settings.GWASCATALOG_DIR, 'gwascatalog-snps-allele-freq-2015-10-09.tsv')  # FIXME
        reader = csv.DictReader(open(catalog_freq_path, 'rb'), delimiter='\t',
                                fieldnames=['snp_id_current', 'allele', 'freq', 'populations'])
        num_created = 0
        num_updated = 0
        for record in reader:
            snp, created = Snp.objects.update_or_create(
                snp_id_current=record['snp_id_current'],
                defaults={'allele': to_null_array_if_blank(record['allele']),
                          'freq': to_null_array_if_blank(record['freq']),
                          'populations': record['populations']}
            )
            if created:
                num_created += 1
            else:
                num_updated += 1

        log.info('updated: {} records'.format(num_updated))
        log.info('created: {} records'.format(num_created))

        # - Gwas Catalog
        log.info('Importing gwascatalog...')
        catalog_path = os.path.join(settings.GWASCATALOG_DIR, 'gwascatalog-cleaned-{}.tsv'.format(today))

        prev = GwasCatalogSnp.objects.filter(date_downloaded=today_with_tz)
        if prev:
            prev.delete()
            log.info('Removed existing records which data_downloaded == today.')

        model_fields = [field for field in GwasCatalogSnp._meta.get_fields() if field.name not in ('id', 'created_at')]
        model_field_names = [field.name for field in model_fields]
        model_fields_map = dict(zip(model_field_names, model_fields))

        gwascatalog_snps = []
        reader = csv.DictReader(open(catalog_path, 'rb'), delimiter='\t')
        for record in reader:
            record.update({'population': get_population(record['initial_sample']),
                           'reliability_rank': '',
                           'odds_ratio': None,
                           'beta_coeff': None})

            # Import only pre-defined in model fields
            data = {}
            for k,v in record.items():
                if k in model_field_names:
                    # Set blank or null
                    if v == '':
                        if type(model_fields_map[k]) in (models.fields.CharField, models.fields.TextField):
                            v = ''
                        else:
                            v = None

                    # Set datetime with timezone
                    if type(model_fields_map[k]) == models.DateTimeField:
                        v = current_tz.localize(datetime(*(parse_date(v).timetuple()[:5])))

                    data[k] = v

            # TODO: odds_ratio/beta_coeff

            # TODO: add freq data for European, African
            population_1st = data['population'][0] if data['population'] else ''
            freq_population = {'EastAsian': '{CHB,JPT}',
                               'European':  '{CHB,JPT}',
                               'African':   '{CHB,JPT}'}.get(population_1st, '{}')

            # TODO: validate risk_allele
            # if freq_population != '{}':
            #     snp = Snp.objects.filter(snp_id_current=data['snp_id_current'], populations=freq_population).first()

            gwascatalog_snps.append(GwasCatalogSnp(**data))

        GwasCatalogSnp.objects.bulk_create(gwascatalog_snps)
        log.info('created: {} records'.format(len(gwascatalog_snps)))

        # - Phenotype
        log.info('Updating phenotype records for gwascatalog...')
        phenotypes = GwasCatalogSnp.objects.distinct().values_list('disease_or_trait', flat=True)
        num_created = 0
        for phenotype in phenotypes:
            gwascatalog_phenotype, created = GwasCatalogPhenotype.objects.get_or_create(
                name=phenotype
            )
            if created:
                num_created += 1
        log.info('created: {} records'.format(num_created))

        log.info('Done.')


def to_null_array_if_blank(text):
    if text == '':
        return '{}'
    else:
        return text
