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

CHROM_CHOICES = [i+1 for i in range(22)] + ['X', 'Y']


class Snp(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    rs_id_reported = models.IntegerField()
    rs_id_current = models.IntegerField()

    chrom = models.CharField(choices=CHROM_CHOICES, blank=True)
    pos = models.IntegerField()
    reference_allele = models.CharField(max_length=1024, blank=True)

    allele = ArrayField(models.CharField(max_length=1024, blank=True))
    east_asian_freq = ArrayField(models.DecimalField(max_digits=1, decimal_places=5))
    european_freq = ArrayField(models.DecimalField())
    african_freq = ArrayField(models.DecimalField())
