import uuid
import datetime

from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.conf import settings
from django.utils.translation import ugettext as _
from django.utils import timezone

from lib.utils import clogging
log = clogging.getColorLogger(__name__)

DECIMAL_PLACES_MAX = 1000

class GwasCatalogSnp(models.Model):
    created_at                     = models.DateTimeField(default=timezone.now)
    is_active                      = models.BooleanField(default=False)

    date_downloaded                = models.DateTimeField()
    pubmed_id                      = models.CharField(max_length=8)
    disease_or_trait               = models.CharField(max_length=1024)
    snp_id                         = models.IntegerField()
    risk_allele                    = models.CharField(max_length=1024, blank=True)

    initial_sample                 = models.CharField(max_length=1024, blank=True)
    chrom_reported                 = models.CharField(max_length=2, blank=True)
    pos_reported                   = models.IntegerField(null=True)
    gene_reported                  = models.CharField(max_length=1024, blank=True)
    risk_allele_freq_reported      = models.FloatField(null=True)
    p_value                        = models.DecimalField(max_digits=DECIMAL_PLACES_MAX, decimal_places=DECIMAL_PLACES_MAX, null=True)
    p_value_text                   = models.CharField(max_length=1024, blank=True)
    odds_ratio_or_beta_coeff       = models.DecimalField(max_digits=8, decimal_places=4, null=True)
    confidence_interval_95_percent = models.CharField(max_length=1024, blank=True)

    reliability_rank               = models.FloatField(null=True)
    population                     = ArrayField(models.CharField(max_length=1024, blank=True))
    odds_ratio                     = models.DecimalField(max_digits=8, decimal_places=4, null=True)
    beta_coeff                     = models.DecimalField(max_digits=8, decimal_places=4, null=True)

    class Meta:
        unique_together = ('date_downloaded', 'pubmed_id', 'disease_or_trait', 'snp_id', 'risk_allele')
