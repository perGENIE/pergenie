import uuid
import datetime

from django.db.models import Model, DateTimeField, BooleanField, CharField, IntegerField, FloatField, DecimalField, ForeignKey
from django.contrib.postgres.fields import ArrayField
from django.conf import settings
from django.utils.translation import ugettext as _
from django.utils import timezone

from apps.snp.models import Snp
from lib.utils import clogging
log = clogging.getColorLogger(__name__)

class GwasCatalogSnp(Model):
    created_at                     = DateTimeField(         default=timezone.now)
    is_active                      = BooleanField(          default=False)

    date_downloaded                = DateTimeField()
    pubmed_id                      = CharField(             max_length=8)
    disease_or_trait               = CharField(             max_length=1024)
    snp_id_reported                = IntegerField(                                                    null=True)
    risk_allele                    = CharField(             max_length=1024,                          blank=True)

    initial_sample                 = CharField(             max_length=1024,                          blank=True)
    chrom_reported                 = CharField(             max_length=2,                             blank=True)
    pos_reported                   = IntegerField(                                                    null=True)
    gene_reported                  = CharField(             max_length=1024,                          blank=True)
    risk_allele_freq_reported      = FloatField(                                                      null=True)
    p_value                        = DecimalField(          max_digits=1000, decimal_places=1000,     null=True)
    p_value_text                   = CharField(             max_length=1024,                          blank=True)
    odds_ratio_or_beta_coeff       = DecimalField(          max_digits=8, decimal_places=4,           null=True)
    confidence_interval_95_percent = CharField(             max_length=1024,                          blank=True)

    reliability_rank               = FloatField(                                                      null=True)
    population                     = ArrayField(CharField(  max_length=1024,                          blank=True))
    odds_ratio                     = DecimalField(          max_digits=8, decimal_places=4,           null=True)
    beta_coeff                     = DecimalField(          max_digits=8, decimal_places=4,           null=True)

    snp = ForeignKey('snp.Snp', null=True)

    class Meta:
        unique_together = ('date_downloaded', 'pubmed_id', 'disease_or_trait', 'snp_id_reported', 'risk_allele')
