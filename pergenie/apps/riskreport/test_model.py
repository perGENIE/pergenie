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

        population = ['EAS']

        # Prepare GwasCatalogSnp
        gwascatalog = [('00000001', 'Type 2 diabetes', 671, 'A', 1.5, population),
                       ('00000001', 'Type 2 diabetes', 672, 'A', 1.5, population),
                       ('00000001', 'Type 2 diabetes', 673, 'A', 1.5, population)]
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
        self.genome = Genome(owner=self.user, file_name='a.vcf', display_name='a.vcf', status=100, population=population[0])
        self.genome.save()

        assert self.genome.population == 'EAS'

    def test_create_riskreport_ok(self):
        # TODO: add more phenotypes
        phenotypes = ['Type 2 diabetes']

        # Prepare Genotype
        gwas_snps = [(671, '{A,A}'),
                     (672, '{A,G}'),
                     (673, '{G,G}')]
        for record in gwas_snps:
            Genotype(genome=self.genome, rs_id_current=record[0], genotype=record[1]).save()

        riskreport, _ = RiskReport.objects.get_or_create(genome=self.genome)
        riskreport.create_riskreport()

        phenotype_risk_repot = PhenotypeRiskReport.objects.filter(risk_report__genome=self.genome)
        assert len(phenotype_risk_repot) == 1
        assert phenotype_risk_repot.get(phenotype__name=phenotypes[0]).estimated_risk == Decimal('1.906')

        snp_risk_reports = SnpRiskReport.objects.filter(phenotype_risk_report__risk_report__genome=self.genome)
        assert len(snp_risk_reports) == 3
        assert snp_risk_reports.get(evidence_snp__snp_id_current=671).estimated_risk == Decimal('1.860')
        assert snp_risk_reports.get(evidence_snp__snp_id_current=672).estimated_risk == Decimal('1.240')
        assert snp_risk_reports.get(evidence_snp__snp_id_current=673).estimated_risk == Decimal('0.8264')
