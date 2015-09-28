import sys
import os
import csv
import datetime

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.conf import settings

from apps.snp.models import Snp
from lib.utils.io import get_url_content
from lib.utils import clogging
log = clogging.getColorLogger(__name__)


class Command(BaseCommand):
    help = "Update SNPs"

    @transaction.atomic
    def handle(self, *args, **options):
        log.info('Fetching latest snps in gwascatalog...')

        if not os.path.exists(settings.GWASCATALOG_DIR):
            os.makedirs(settings.GWASCATALOG_DIR)

        today = datetime.datetime.now().strftime('%Y-%m-%d')
        af_path = os.path.join(settings.GWASCATALOG_DIR, 'gwascatalog_snps_allele_freq_{}.tsv'.format(today))

        log.info('Importing snps in gwascatalog...')

        chunk_length = 1000
        snps = []

        fields = ('rs_id_reported', 'rs_id_current', 'allele', 'freq', 'populations')
        reader = csv.DictReader(open(af_path, 'rb'), delimiter='\t', fieldnames=fields)
        for record in reader:
            snps.append(Snp(**record))

            if len(snps) == chunk_length:
                Snp.objects.bulk_create(snps)
                snps[:] = []

        if len(snps) > 0:
            Snp.objects.bulk_create(snps)

        log.info('Done.')
