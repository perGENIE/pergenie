from django.db import models
from django.db.models import Max
from django.utils import timezone
from django.utils.translation import get_language
from django.conf import settings

from celery.task import Task
from celery.decorators import task
from celery.exceptions import Ignore

from apps.authentication.models import User
from apps.genome.models import Genome
from apps.gwascatalog.models import GwasCatalogPhenotype, GwasCatalogSnp
from apps.snp.models import Snp, get_freqs
from lib.riskreport.commons import *
from utils import clogging
log = clogging.getColorLogger(__name__)


class RiskReport(models.Model):
    '''
     ------------
    |            |
    |   Genome   |
    |            |
     ------------
          1
          |
          n
     ------------       ---------------------       ---------------
    |            |     |                     |     |               |
    | RiskReport |1 - n| PhenotypeRiskReport |1 - n| SnpRiskReport |
    |            |     |                     |     |               |
     ------------       ---------------------       ---------------
                                  1                        1
                                  |                        |
                                  1                        1
                        ----------------------      ----------------
                       |                      |    |                |
                       | GwasCatalogPhenotype |    | GwasCatalogSnp |
                       |                      |    |                |
                        ----------------------      ----------------
    '''

    created_at = models.DateTimeField(default=timezone.now)
    genome = models.ForeignKey(Genome)
    # display_name =

    def create_riskreport(self):
        task_create_riskreport.delay(self.genome)

class PhenotypeRiskReport(models.Model):
    risk_report = models.ForeignKey(RiskReport)
    phenotype = models.ForeignKey(GwasCatalogPhenotype)

    estimated_risk = models.DecimalField(max_digits=5, decimal_places=4)

    class Meta:
        unique_together = ('risk_report', 'phenotype')

class SnpRiskReport(models.Model):
    phenotype_risk_report = models.ForeignKey(PhenotypeRiskReport)
    evidence_snp = models.ForeignKey(GwasCatalogSnp)

    estimated_risk = models.DecimalField(max_digits=5, decimal_places=4)
    # genotype_ee_risk =
    # genotype_en_risk =
    # genotype_nn_risk =
    # genotype_avg_risk =

    class Meta:
        unique_together = ('phenotype_risk_report', 'evidence_snp')

@task(ignore_result=True)
def task_create_riskreport(genome):
    log.info('Creating riskreport ...')

    # TODO: Check for updates
    latest_date = GwasCatalogSnp.objects.filter().aggregate(Max('date_downloaded'))['date_downloaded__max']

    phenotypes = GwasCatalogPhenotype.objects.all()
    population = Genome.POPULATION_MAP[genome.population]

    for phenotype in phenotypes:
        gwas_snps = GwasCatalogSnp.objects.filter(disease_or_trait=phenotype,
                                                  population__contains=population,
                                                  date_downloaded=str(latest_date))

        # Select only one article for one phenotype
        #
        # TODO: add conditions
        # - risk alleles are present
        # - odds ratios are present
        # - lower than minimum p-value
        evidence_article_1st = gwas_snps.order_by('reliability_rank').values_list('pubmed_id', flat=True).first()
        evidence_snps = gwas_snps.filter(pubmed_id=evidence_article_1st).values()
        evidence_snp_ids = evidence_snps.values_list('snp_id_current', flat=True)

        freqs = get_freqs(evidence_snp_ids)
        genotype = ''.join(Genotype.objects.filter(genome__id=genome_id,
                                                    rs_id_current__in=evidence_snp_ids).values())

        phenotype_risk_report = PhenotypeRiskReport.objects.get_or_create(risk_report=risk_report, phenotype=phenotype)

        # Calculate cumulative risk
        estimated_snp_risks = []

        for evidence_snp in evidence_snps:
            risk_allele_forward = evidence_snp.get('risk_allele_forward')
            risk_allele_freq = freqs.get(evidence_snp.get('snp_id_current')).get(risk_allele_forward)
            odds_ratio = evidence_snp.get('odds_ratio')
            zygosities = zyg(genotype, risk_allele_forward)
            estimated_risk = relative_risk_to_general_population(risk_allele_freq, odds_ratio, zygosities)
            estimated_snp_risks.append(estimated_risk)

            SnpRiskReport(phenotype_risk_report=phenotype_riskreport,
                          evidence_snp=evidence_snp,
                          estimated_risk=estimated_risk)

        phenotype_risk_report.estimated_risk = cumulative_risk(estimated_snp_risks)
        phenotype_risk_report.save()
