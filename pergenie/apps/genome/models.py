from uuid import uuid4

from django.db import models
from django.utils.translation import ugettext as _

from apps.authentication.models import User


class Genome(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    owners = models.ManyToManyField(User, related_name='owner')
    readers = models.ManyToManyField(User, related_name='reader')

    file_name = models.FilePathField(max_length=100)
    display_name = models.CharField(max_length=100)

    FILE_FORMAT_VCF = 'VCF'
    FILE_FORMAT_23ANDME = 'ANDME'
    FILE_FORMAT_CHOICES = [
        (FILE_FORMAT_VCF, 'VCF'),
        (FILE_FORMAT_23ANDME, '23andMe CSV'),
    ]
    file_format = models.CharField(max_length=5,
                                   choices=FILE_FORMAT_CHOICES,
                                   default=FILE_FORMAT_VCF)

    POPULATION_ASIAN = 'ASN'
    POPULATION_EUROPEAN = 'EUR'
    POPULATION_AFRICAN = 'AFR'
    POPULATION_JAPANESE = 'JPN'
    POPULATION_UNKNOWN = 'UN'
    POPULATION_CHOICES = [
        (POPULATION_UNKNOWN, _('unknown')),
        (POPULATION_ASIAN, _('Asian')),
        (POPULATION_EUROPEAN, _('European')),
        (POPULATION_AFRICAN, _('African')),
        (POPULATION_JAPANESE, _('Japanese')),
    ]
    population = models.CharField(max_length=3,
                                  choices=POPULATION_CHOICES,
                                  default=POPULATION_UNKNOWN)

    SEX_MALE = 'M'
    SEX_FEMALE = 'F'
    SEX_UNKNOWN = 'U'
    SEX_CHOICES = [
        (SEX_UNKNOWN, _('unknown')),
        (SEX_MALE, _('Male')),
        (SEX_FEMALE, _('Female')),
    ]
    sex = models.CharField(max_length=1,
                           choices=SEX_CHOICES,
                           default=SEX_UNKNOWN)

    status = models.IntegerField(default=0)
