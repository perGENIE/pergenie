import sys
import os
import csv
from glob import glob
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.db import models, transaction
from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_date

from apps.snp.models import Snp
from apps.gwascatalog.models import GwasCatalogSnp, GwasCatalogPhenotype
from cleanup.population import get_population
from cleanup.odds_ratio_or_beta_coeff import get_odds_ratio_or_beta_coeff, get_ci_and_unit
from cleanup.errors import GwasCatalogParseError
from cleanup.reliability_rank import get_reliability_rank
from cleanup.risk_allele import get_database_strand_allele, AMBIGOUS
from lib.utils.io import get_url_content
from lib.utils.pg import text2pg_array
from lib.utils import clogging
log = clogging.getColorLogger(__name__)


class Command(BaseCommand):
    help = "Update GWAS Catalog"

    def handle(self, *args, **options):
        current_tz = timezone.get_current_timezone()
        today = timezone.now().strftime('%Y-%m-%d')
        today_with_tz = current_tz.localize(datetime(*(parse_date(today).timetuple()[:5])))

        if not os.path.exists(settings.GWASCATALOG_DIR):
            os.makedirs(settings.GWASCATALOG_DIR)

        # TODO: automatically choose latest version
        log.info('Fetching latest gwascatalog...')
        catalog_path = os.path.join(settings.GWASCATALOG_DIR, 'dbsnp-pg-min-0.5.1-b144-GRCh37.gwascatalog-cleaned.tsv')
        get_url_content(url='https://github.com/knmkr/dbsnp-pg-min/releases/download/0.5.1/dbsnp-pg-min-0.5.1-b144-GRCh37.gwascatalog-cleaned.tsv',
                        dst=catalog_path,
                        if_not_exists=True)

        log.info('Fetching latest gwascatalog allele freq...')
        catalog_freq_path = os.path.join(settings.GWASCATALOG_DIR, 'dbsnp-pg-min-0.5.1-b144-GRCh37.gwascatalog-snps-allele-freq.tsv')
        get_url_content(url='https://github.com/knmkr/dbsnp-pg-min/releases/download/0.5.1/dbsnp-pg-min-0.5.1-b144-GRCh37.gwascatalog-snps-allele-freq.tsv',
                        dst=catalog_freq_path,
                        if_not_exists=True)

        # - Gwas Catalog Allele Freq
        log.info('Updating snp allele freq records for gwascatalog...')
        num_created = 0
        num_updated = 0

        with transaction.atomic():
            for record in csv.DictReader(open(catalog_freq_path, 'rb'), delimiter='\t',
                                         fieldnames=['snp_id_current', 'allele', 'freq', 'populations']):
                snp, created = Snp.objects.update_or_create(
                    snp_id_current=record['snp_id_current'],
                    defaults={'allele': text2pg_array(record['allele']),
                              'freq': text2pg_array(record['freq']),
                              'population': record['populations']}
                )
                if created:
                    num_created += 1
                else:
                    num_updated += 1

        log.info('updated: {} records'.format(num_updated))
        log.info('created: {} records'.format(num_created))

        # - Gwas Catalog
        log.info('Importing gwascatalog...')
        model_fields = [field for field in GwasCatalogSnp._meta.get_fields() if field.name not in ('id', 'created_at')]
        model_field_names = [field.name for field in model_fields]
        model_fields_map = dict(zip(model_field_names, model_fields))

        gwascatalog_snps = []
        num_phenotype_created = 0

        for record in csv.DictReader(open(catalog_path, 'rb'), delimiter='\t'):
            data = {}

            # If date_downloaded is already imported, abort.
            date_downloaded = record['date_downloaded']
            if GwasCatalogSnp.objects.filter(date_downloaded=date_downloaded).exists():
                raise GwasCatalogParseError('Already imported date_downloaded: {}'.format(date_downloaded))

            # Import only pre-defined model fields
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

            # Parse population
            population       = get_population(record['initial_sample'])

            # Calculate reliability rank
            reliability_rank = 1.0  # TODO: get_reliability_rank()

            try:
                # Parse and validate odds_ratio, beta_coeff
                _, unit                = get_ci_and_unit(record['confidence_interval_95_percent'])
                odds_ratio, beta_coeff = get_odds_ratio_or_beta_coeff(record['odds_ratio_or_beta_coeff'], unit)

                # Validate risk_allele
                #
                # Strands of risk alleles in GWAS Catalog are not set to forward strands with respect to
                # the human reference genome b37. So we get forward strand alleles by checking consistences of
                # allele frequencies between reported risk alleles and 1000 Genomes Project alleles.
                if data['snp_id_current']:
                    # TODO: change freq source by population
                    snp = Snp.objects.filter(snp_id_current=data['snp_id_current']).first()
                    database_freq = dict(zip(snp.allele, snp.freq))
                    risk_allele_forward = get_database_strand_allele(record['risk_allele'], record['risk_allele_freq_reported'],
                                                                     database_freq, freq_diff_thrs=settings.GWASCATALOG_FREQ_DIFF_THRS)
                else:
                    risk_allele_forward = AMBIGOUS

                is_active = True

            except GwasCatalogParseError as e:
                odds_ratio, beta_coeff = None, None
                is_active = False

            # - Phenotype
            phenotype, phenotype_created = GwasCatalogPhenotype.objects.get_or_create(name=record['disease_or_trait'])
            if phenotype_created:
                num_phenotype_created += 1

            data.update({'population':          population,
                         'reliability_rank':    reliability_rank,
                         'odds_ratio':          odds_ratio,
                         'beta_coeff':          beta_coeff,
                         'beta_coeff_unit':     unit,
                         'risk_allele_forward': risk_allele_forward,
                         'phenotype':           phenotype,
                         'is_active':           is_active})

            gwascatalog_snps.append(GwasCatalogSnp(**data))
            # GwasCatalogSnp.objects.create(**data)

        with transaction.atomic():
            GwasCatalogSnp.objects.bulk_create(gwascatalog_snps)

        log.info('GWAS Catalog snps processed: {} records'.format(len(gwascatalog_snps)))
        log.info('GWAS Catalog phenotypes newly created: {} records'.format(num_created))

        log.info('Done.')
