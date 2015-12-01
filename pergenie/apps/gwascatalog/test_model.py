from datetime import timedelta

from django.test import TestCase

from .models import GwasCatalogSnp, GwasCatalogPhenotype
from lib.utils.date import today_with_tz


class GWASCatalogModelTestCase(TestCase):
    def setUp(self):
        self.today_with_tz = today_with_tz
        population = ['EAS']

        # Setup 3 records (date = today)
        gwascatalog = [('00000001', 'Type 2 diabetes', 671, 'A', 1.5, population),
                       ('00000001', 'Type 2 diabetes', 672, 'A', 1.5, population),
                       ('00000001', 'Type 2 diabetes', 673, 'A', 1.5, population)]

        for record in gwascatalog:
            phenotype, _ = GwasCatalogPhenotype.objects.get_or_create(name=record[1])
            GwasCatalogSnp(date_downloaded=self.today_with_tz,
                           pubmed_id=record[0],
                           phenotype=phenotype,
                           snp_id_current=record[2],
                           risk_allele_forward=record[3],
                           odds_ratio=record[4],
                           population=record[5]).save()

        # Setup 1 records (date = tomorrow)
        self.tomorrow = self.today_with_tz + timedelta(days=1)
        record = ('00000001', 'Type 2 diabetes', 671, 'A', 2.0, population)
        phenotype, _ = GwasCatalogPhenotype.objects.get_or_create(name=record[1])
        GwasCatalogSnp(date_downloaded=self.tomorrow,
                       pubmed_id=record[0],
                       phenotype=phenotype,
                       snp_id_current=record[2],
                       risk_allele_forward=record[3],
                       odds_ratio=record[4],
                       population=record[5]).save()

        assert len(GwasCatalogPhenotype.objects.all()) == 1
        assert len(GwasCatalogSnp.objects.all()) == 4

    def test_gwascatalog_create_ok(self):
        population = ['EAS']
        record = ('00000001', 'Type 2 diabetes', 674, 'A', 1.5, population)
        phenotype, _ = GwasCatalogPhenotype.objects.get_or_create(name=record[1])
        GwasCatalogSnp(date_downloaded=self.today_with_tz,
                       pubmed_id=record[0],
                       phenotype=phenotype,
                       snp_id_current=record[2],
                       risk_allele_forward=record[3],
                       odds_ratio=record[4],
                       population=record[5]).save()

        assert len(GwasCatalogPhenotype.objects.all()) == 1
        assert len(GwasCatalogSnp.objects.all()) == 5

    def test_gwascatalog_delete_ok(self):
        GwasCatalogSnp.objects.filter(date_downloaded=self.today_with_tz).delete()

        assert len(GwasCatalogPhenotype.objects.all()) == 1
        assert len(GwasCatalogSnp.objects.all()) == 1

    def test_gwascatalog_get_latest_ok(self):
        catalog = GwasCatalogSnp.objects.latest('date_downloaded')
        assert catalog.date_downloaded == self.tomorrow
