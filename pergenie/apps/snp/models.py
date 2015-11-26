import os
import sys
import uuid
import datetime

from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.conf import settings
from django.utils.translation import ugettext as _

from lib.utils import clogging
log = clogging.getColorLogger(__name__)

_chrom = [i+1 for i in range(22)] + ['X', 'Y']
CHROM_CHOICES = zip(_chrom, _chrom)


class Snp(models.Model):
    snp_id_current = models.IntegerField()

    allele = ArrayField(models.CharField(max_length=1024))
    freq = ArrayField(models.DecimalField(max_digits=5, decimal_places=4))
    population = ArrayField(models.CharField(max_length=32))

    chrom = models.CharField(choices=CHROM_CHOICES, max_length=2, blank=True)
    pos = models.IntegerField(null=True, blank=True)

    class Meta:
        unique_together = ('snp_id_current', 'population')

def get_freqs(snp_ids):
    """Return allele freq records as dictionary instead of ValuesQuerySet.

    Example

    ```
    {671: {u'A': Decimal('0.2000'), u'G': Decimal('0.8000')},
     672: {u'A': Decimal('0.2000'), u'G': Decimal('0.8000')},
     673: {u'A': Decimal('0.2000'), u'G': Decimal('0.8000')}}

    # ValuesQuerySet
    # [{'allele': [u'A', u'G'], 'freq': [Decimal('0.2000'), Decimal('0.8000')], 'snp_id_current': 671},
    # {'allele': [u'A', u'G'], 'freq': [Decimal('0.2000'), Decimal('0.8000')], 'snp_id_current': 672},
    # {'allele': [u'A', u'G'], 'freq': [Decimal('0.2000'), Decimal('0.8000')], 'snp_id_current': 673}]
    ```
    """

    snps = Snp.objects.filter(snp_id_current__in=snp_ids).values()
    freqs = {x['snp_id_current']: dict(zip(x['allele'], x['freq'])) for x in freqs.values()}
    return freqs
