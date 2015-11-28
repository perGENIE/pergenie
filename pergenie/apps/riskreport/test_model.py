from decimal import Decimal

from django.test import TestCase
from django.test.utils import override_settings

from apps.authentication.models import User
from apps.gwascatalog.models import GwasCatalogSnp, GwasCatalogPhenotype
from apps.snp.models import Snp
from apps.genome.models import Genome, Genotype
from .models import RiskReport, PhenotypeRiskReport, SnpRiskReport
from lib.utils.date import today_with_tz
from lib.utils import clogging
log = clogging.getColorLogger(__name__)


@override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                   CELERY_ALWAYS_EAGER=True,
                   BROKER_BACKEND='memory')
class RiskReportModelTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('test-user@pergenie.org', 'test-user-password')
        self.user.is_active = True
        self.user.save()

        population = ['EastAsian']

        # Prepare GwasCatalogSnp
        gwascatalog = [('00000001', 'Type 2 diabetes', 671, 'A', 2.0, population),
                       ('00000001', 'Type 2 diabetes', 672, 'A', 2.0, population),
                       ('00000001', 'Type 2 diabetes', 673, 'A', 2.0, population)]
        for record in gwascatalog:
            phenotype, _ = GwasCatalogPhenotype.objects.get_or_create(name=record[1])
            GwasCatalogSnp(date_downloaded=today_with_tz,
                           pubmed_id=record[0],
                           phenotype=phenotype,
                           snp_id_current=record[2],
                           risk_allele_forward=record[3],
                           odds_ratio=record[4],
                           population=record[5]).save()

        assert len(GwasCatalogPhenotype.objects.all()) == 1
        assert len(GwasCatalogSnp.objects.all()) == 3

        # Prepare Snp
        freq = [(671, ['A','G'], [0.2,0.8], population),
                (672, ['A','G'], [0.2,0.8], population),
                (673, ['A','G'], [0.2,0.8], population)]
        for record in freq:
            Snp(snp_id_current=record[0],
                allele=record[1],
                freq=[Decimal(x) for x in record[2]],
                population=record[3]).save()

        assert len(Snp.objects.all()) == 3

        # Prepare Genome
        self.genome = Genome(owner=self.user, file_name='a.vcf', display_name='a.vcf', status=100, population=Genome.POPULATION_MAP_REVERSE[population[0]])
        self.genome.save()

        assert self.genome.population == 'ASN'

    def test_create_riskreport_ok(self):
        # Prepare Genotype
        gwas_snps = [(671, '{A,A}'),
                     (672, '{A,A}'),
                     (673, '{A,A}')]
        for record in gwas_snps:
            Genotype(genome=self.genome, rs_id_current=record[0], genotype=record[1]).save()

        riskreport, _ = RiskReport.objects.get_or_create(genome=self.genome)
        riskreport.create_riskreport()

        assert len(PhenotypeRiskReport.objects.filter(risk_report__genome=self.genome)) == 1
        assert len(SnpRiskReport.objects.filter(phenotype_risk_report__risk_report__genome=self.genome)) == 3
