import uuid
import datetime

from django.db import models
from django.conf import settings
from django.utils.translation import ugettext as _

from lib.utils import clogging
log = clogging.getColorLogger(__name__)


class GwasCatalogSnp(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(default=datetime.datetime.now)
    is_active = models.BooleanField(default=False)

    # date_added                     = models.DateTimeField()
    pubmed_id                      = models.CharField()
    # first_author                   = models.CharField()
    # date_published                 = models.DateTimeField()
    # journal                        = models.CharField()
    # pubmed_url                     = models.CharField()
    # study_title                    = models.CharField()
    disease_or_trait               = models.CharField()
    initial_sample                 = models.CharField()
    # replication_sample             = models.CharField()
    # region                         = models.CharField()
    chrom                          = models.CharField()
    pos                            = models.IntegerField()
    gene_reported                  = models.CharField()
    # gene_mapped                    = models.CharField()
    # upstream_entrez_gene_id        = models.CharField()
    # downstream_entrez_gene_id      = models.CharField()
    # entrez_gene_id                 = models.CharField()
    # upstream_gene_distance_kb      = models.FloatField()
    # downstream_gene_distance_kb    = models.FloatField()
    # strongest_snp_risk_allele      = models.CharField()
    # strongest_snps                 = models.CharField()
    # is_snp_id_merged               = models.NullBooleanField()
    # snp_id_current                 = models.CharField()
    # snp_context                    = models.CharField()
    # is_snp_intergenic              = models.NullBooleanField()
    risk_allele_freq_reported      = models.FloatField()
    p_value                        = models.DecimalField()
    # minus_log_p_value              = models.FloatField()
    p_value_text                   = models.CharField()
    odds_ratio_or_beta_coeff       = models.DecimalField()
    confidence_interval_95_percent = models.CharField()
    # snp_platform                   = models.CharField()
    # cnv                            = models.CharField()
    snp_id                         = models.IntegerField()
    risk_allele                    = models.CharField(max_length=1024)
    date_downloaded                = models.DateTimeField()

    reliability_rank               = models.FloatField()
    population                     = models.CharField()
    odds_ratio                     = models.FloatField()
    beta_coeff                     = models.FloatField()

    class Meta:
        unique_together = ('date_downloaded', 'pubmed_id', 'disease_or_trait', 'snp_id', 'risk_allele')
