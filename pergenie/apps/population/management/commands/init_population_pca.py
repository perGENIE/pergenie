import os
import glob

from django.core.management.base import BaseCommand
from django.conf import settings

from apps.population.models import PopulationPcaGeoPoint
from lib.utils import clogging
log = clogging.getColorLogger(__name__)


class Command(BaseCommand):
    help = "Init Population PCA"

    def handle(self, *args, **options):
        log.info('Init Population PCA data ...')

        # Import snp id of each PCA coordinate
        for src in glob.glob(os.path.join(settings.BASE_DIR, 'lib', 'population', '*.csv')):
            log.info('Importing snp id data ...')
            log.info(src)

            # FIXME: DRY
            geo_source = os.path.basename(src).replace('.geo', '')

            with open(src, 'r') as fin:
                for i, line in enumerate(fin):
                    if i == 0:
                        data = {}
                        PopulationPcaSnp.objects.create(**data)
                        break
                    # TBD: Import original metrix data .csv

        # Import geometric points of people in each PCA coordinate.
        for src in glob.glob(os.path.join(settings.BASE_DIR, 'lib', 'population', '*.geo')):
            log.info('Importing genometric points data ...')
            log.info(src)

            geo_source = os.path.basename(src).replace('.geo', '')

            with open(src, 'r') as fin:
                for line in fin:
                    num, pc_1, pc_2, population_code = line.rstrip().split(',')

                    if num == '':
                        continue

                    data = dict(geo_source=geo_source,
                                population_code=population_code,
                                pc_1=float(pc_1),
                                pc_2=float(pc_2))

                    PopulationPcaGeoPoint.objects.create(**data)

        log.info('Done.')
