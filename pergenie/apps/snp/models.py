import os
import sys
import uuid
import datetime

from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.conf import settings
from django.utils.translation import ugettext as _

from lib.utils.population import POPULATION_CHOICES, POPULATION_GLOBAL, POPULATION_EUROPEAN, POPULATION_AFRICAN, POPULATION_EAST_ASIAN
from lib.utils.genome import CHROM_CHOICES
from lib.utils import clogging
log = clogging.getColorLogger(__name__)


class Snp(models.Model):
    snp_id_current = models.IntegerField()

    allele = ArrayField(models.CharField(max_length=1024))
    freq = ArrayField(models.DecimalField(max_digits=5, decimal_places=4))
    population = ArrayField(models.CharField(choices=POPULATION_CHOICES, max_length=3))

    chrom = models.CharField(choices=CHROM_CHOICES, max_length=2, blank=True)
    pos = models.IntegerField(null=True, blank=True)

    class Meta:
        unique_together = ('snp_id_current', 'population')


def get_freqs(snp_ids, population=[POPULATION_GLOBAL]):
    """Return allele freq records as dictionary instead of ValuesQuerySet.

    Args
    - list<int> snp_ids: query snp ids
    - list<str> population: query population code

    Example

    ```
    # >>> get_freqs([671], ['EAS'])
    # {671: {u'A': Decimal('0.2000'), u'G': Decimal('0.8000')},
    #  672: {u'A': Decimal('0.2000'), u'G': Decimal('0.8000')},
    #  673: {u'A': Decimal('0.2000'), u'G': Decimal('0.8000')}}
    ```
    """

    #
    if set(population) == set([POPULATION_EUROPEAN, POPULATION_AFRICAN, POPULATION_EAST_ASIAN]):
        population = [POPULATION_GLOBAL]

    snps = Snp.objects.filter(snp_id_current__in=snp_ids, population__overlap=population).values()

    # Map ValuesQuerySet to dict
    #
    # ValuesQuerySet:
    # [{'allele': [u'A', u'G'], 'freq': [Decimal('0.2000'), Decimal('0.8000')], 'snp_id_current': 671},
    # {'allele': [u'A', u'G'], 'freq': [Decimal('0.2000'), Decimal('0.8000')], 'snp_id_current': 672},
    # {'allele': [u'A', u'G'], 'freq': [Decimal('0.2000'), Decimal('0.8000')], 'snp_id_current': 673}]
    #
    # dict:
    # {671: {u'A': Decimal('0.2000'), u'G': Decimal('0.8000')},
    #  672: {u'A': Decimal('0.2000'), u'G': Decimal('0.8000')},
    #  673: {u'A': Decimal('0.2000'), u'G': Decimal('0.8000')}}
    freqs = {x['snp_id_current']: dict(zip(x['allele'], x['freq'])) for x in snps.values()}
    return freqs
