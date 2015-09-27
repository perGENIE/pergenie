import sys
import os
import csv
import datetime

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from apps.gwascatalog.models import GwasCatalogSnp
from lib.utils.io import get_url_content
from lib.utils import clogging
log = clogging.getColorLogger(__name__)


class Command(BaseCommand):
    help = "Update GWAS Catalog"

    def handle(self, *args, **options):
        try:
            log.info('Fetching latest gwascatalog...')

            if not os.path.exists(GWASCATALOG_DIR):
                os.makedirs(GWASCATALOG_DIR)

            today = datetime.datetime.now().strftime('%Y-%m-%d')
            catalog_path = os.path.join(GWASCATALOG_DIR, 'gwascatalog.{}.tsv'.format(today))

            if not os.path.exists(catalog_path):
                try:
                    get_url_content(url=settings.GWASCATALOG_URL, dst=catalog_path)
                except (IOError,KeyboardInterrupt) as exception:
                    if os.path.exists(catalog_path):
                        os.remove(catalog_path)
                    raise

            log.info('Importing gwascatalog...')

            chunk_length = 1000
            gwascatalog_snps = []

            reader = csv.DictReader(catalog_path, delimiter='\t')
            for record in reader:

                population = get_population(record['initial_sample_size'])

                if population:
                    population_1st = population[0]
                    db_allele_freq = {'Asian': {}, 'European': {}, 'African': {}}[population_1st]  # TODO
                else:
                    db_allele_freq = {}

                # TODO: odds_ratio/beta_coeff

                record.update({'risk_allele_forward': get_forward_risk_allele(record['risk_allele'],
                                                                              record['risk_allele_freq_reported'],
                                                                              db_allele_freq,
                                                                              settings.GWASCATALOG_INCONSISTENCE_THRS),
                               'population': population,
                               'reliability_rank': get_reliability_rank(record['study'],
                                                                        record['p_value'])}

                snp = GwasCatalogSnp(**record)
                gwascatalog_snps.append(snp)

                if len(gwascatalog_snps) == chunk_length:
                    GwasCatalogSnp.object.bulk_create(gwascatalog_snps)
                    gwascatalog_snps[:] = []

            if len(gwascatalog_snps) > 0:
                GwasCatalogSnp.object.bulk_create(gwascatalog_snps)

            log.info('Done.')

        except Exception as exception:
            # TODO: rollback
            # catalog.delete_catalog()
            # catalog.delete()
            raise
