from django.db import models
from django.db.models import Max
from django.utils import timezone

from celery.decorators import task

from apps.genome.models import Genome, Genotype
from apps.gwascatalog.models import GwasCatalogPhenotype, GwasCatalogSnp
from apps.snp.models import get_freqs
from lib.riskreport.commons import *
from lib.utils.pg import list2pg_array
from utils import clogging
log = clogging.getColorLogger(__name__)


class RiskReport(models.Model):
    """
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
    """

    created_at = models.DateTimeField(default=timezone.now)
    genome = models.ForeignKey(Genome)
    # display_name =

    def create_riskreport(self):
        task_create_riskreport.delay(self, self.genome)


class PhenotypeRiskReport(models.Model):
    risk_report = models.ForeignKey(RiskReport)
    phenotype = models.ForeignKey(GwasCatalogPhenotype)

    estimated_risk = models.DecimalField(max_digits=5, decimal_places=4, default=1.0)

    class Meta:
        unique_together = ('risk_report', 'phenotype')


class SnpRiskReport(models.Model):
    phenotype_risk_report = models.ForeignKey(PhenotypeRiskReport)
    evidence_snp = models.ForeignKey(GwasCatalogSnp)

    estimated_risk = models.DecimalField(max_digits=5, decimal_places=4, default=1.0)
    # genotype_ee_risk =
    # genotype_en_risk =
    # genotype_nn_risk =
    # genotype_avg_risk =

    class Meta:
        unique_together = ('phenotype_risk_report', 'evidence_snp')


@task(ignore_result=True)
def task_create_riskreport(risk_report, genome):
    log.info('Creating riskreport ...')

    # TODO: Check for updates
    latest_date = GwasCatalogSnp.objects.filter().aggregate(Max('date_downloaded'))['date_downloaded__max']

    phenotypes = GwasCatalogPhenotype.objects.all()
    log.debug('#phenotypes: {}'.format(len(phenotypes)))

    population = list2pg_array([Genome.POPULATION_MAP[genome.population]])

    for phenotype in phenotypes:
        assert type(phenotype) == GwasCatalogPhenotype
        gwas_snps = GwasCatalogSnp.objects.filter(phenotype=phenotype,
                                                  population__contains=population,
                                                  date_downloaded=str(latest_date))

        # Select only one article for one phenotype
        #
        # TODO: add conditions
        # - risk alleles are present
        # - odds ratios are present
        # - lower than minimum p-value
        evidence_article_1st = gwas_snps.order_by('reliability_rank').values_list('pubmed_id', flat=True).first()
        evidence_snps = gwas_snps.filter(pubmed_id=evidence_article_1st)
        evidence_snp_ids = evidence_snps.values_list('snp_id_current', flat=True)

        freqs = get_freqs(evidence_snp_ids)
        genotypes = Genotype.objects.filter(genome__id=genome.id, rs_id_current__in=evidence_snp_ids)

        phenotype_risk_report, _ = PhenotypeRiskReport.objects.get_or_create(risk_report=risk_report, phenotype=phenotype)

        # Calculate cumulative risk
        estimated_snp_risks = []

        # Genotype specific risks for each SNP
        for evidence_snp in evidence_snps:
            # TODO: case: if risk_allele/freq/genotype/ not found

            # Risk allele and its frequency
            risk_allele_forward = evidence_snp.risk_allele_forward
            risk_allele_freq = freqs.get(evidence_snp.snp_id_current).get(risk_allele_forward)
            odds_ratio = evidence_snp.odds_ratio

            # My genotype
            genotype = ''.join(genotypes.get(rs_id_current=evidence_snp.snp_id_current).genotype)
            zygosities = zyg(genotype, risk_allele_forward)

            # Genotype specific risks
            genotype_specific_risks = genotype_specific_risks_relative_to_population(risk_allele_freq, odds_ratio)
            my_estimated_risk = estimated_risk(genotype_specific_risks, zygosities)

            SnpRiskReport(phenotype_risk_report=phenotype_risk_report,
                          evidence_snp=evidence_snp,
                          estimated_risk=my_estimated_risk).save()

            estimated_snp_risks.append(my_estimated_risk)

        phenotype_risk_report.estimated_risk = cumulative_risk(estimated_snp_risks)
        phenotype_risk_report.save()
