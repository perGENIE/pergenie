import os
import glob

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

# from apps.snp.models import PopulationPcaSnp
from apps.population.models import PopulationPcaGeoPoint
from lib.utils import clogging
log = clogging.getColorLogger(__name__)


class Command(BaseCommand):
    help = "Init Population PCA"

    def handle(self, *args, **options):
        log.info('Init Population PCA data ...')

        for population in ['global']:
            try:
                # Import snp id of each PCA coordinate
                # csv = os.path.join(settings.BASE_DIR, 'lib', 'population', 'csv', '1000genomes.{}.subsnps.csv'.format(population))
                # log.info('Importing snp id data ...')
                # log.info(csv)
                #
                # record = PopulationPcaSnp.objects.filter(src=os.path.basename(csv))
                # if record:
                #     raise CommandError('Abort. Already imported src: {}'.format(csv))
                #
                # with open(csv, 'r') as fin:
                #     for i, line in enumerate(fin):
                #         if i == 0:
                #             for snp in line.split(',')[:-1]:
                #                 PopulationPcaSnp.objects.create(src=os.path.basename(csv),
                #                                                 snp_id_used=int(snp[2:-2]),
                #                                                 snp_id_current=int(snp[2:-2]),  # FIXME: Need to update rs id
                #                                                 ref=snp[-2:-1],
                #                                                 alt=snp[-1])
                #             break
                #         # TBD: Import original metrix data .csv

                # Import geometric points of people in each PCA coordinate.
                geo = os.path.join(settings.BASE_DIR, 'lib', 'population', 'geo', '{}.geo'.format(population))
                log.info('Importing genometric points data ...')
                log.info(geo)

                record = PopulationPcaGeoPoint.objects.filter(src=os.path.basename(geo))
                if record:
                    raise CommandError('Abort. Already imported src: {}'.format(geo))

                with open(geo, 'r') as fin:
                    for line in fin:
                        num, pc_1, pc_2, population_code = line.rstrip().split(',')

                        if num == '':
                            continue

                        data = dict(src=os.path.basename(geo),
                                    population_code=population_code,
                                    pc_1=float(pc_1),
                                    pc_2=float(pc_2))

                        PopulationPcaGeoPoint.objects.create(**data)
            except CommandError as e:
                log.error(e)

        log.info('Done.')
