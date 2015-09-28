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
    rs_id_reported = models.IntegerField()
    rs_id_current = models.IntegerField()

    allele = ArrayField(models.CharField(max_length=1024))
    freq = ArrayField(models.DecimalField(max_digits=5, decimal_places=4))
    populations = ArrayField(models.CharField(max_length=32))

    chrom = models.CharField(choices=CHROM_CHOICES, max_length=2, blank=True)
    pos = models.IntegerField(null=True, blank=True)

    class Meta:
        unique_together = ('rs_id_reported', 'rs_id_current', 'populations')
