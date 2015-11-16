from django.db import models
from django.utils import timezone

from django.utils.translation import get_language
from django.conf import settings

from apps.genome.models import Genome
from apps.gwascatalog.models import GwasCatalogPhenotype, GwasCatalogSnp
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

class PhenotypeRiskReport(models.Model):
    risk_report = models.ForeignKey(RiskReport)
    phenotype = models.ForeignKey(GwasCatalogPhenotype)

    # estimated_risk = float

class SnpRiskReport(models.Model):
    phenotype_risk_report = models.ForeignKey(PhenotypeRiskReport)
    snp = models.ForeignKey(GwasCatalogSnp)

    # estimated_risk = float
    # genotype_ee_risk =
    # genotype_en_risk =
    # genotype_nn_risk =
    # genotype_avg_risk =
