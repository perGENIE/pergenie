# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.contrib.postgres.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Snp',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('snp_id_current', models.IntegerField()),
                ('allele', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=1024), size=None)),
                ('freq', django.contrib.postgres.fields.ArrayField(base_field=models.DecimalField(max_digits=5, decimal_places=4), size=None)),
                ('population', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=3, choices=[(b'UN', 'Unknown'), (b'EAS', 'EastAsian'), (b'EUR', 'European'), (b'AFR', 'African')]), size=None)),
                ('chrom', models.CharField(blank=True, max_length=2, choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 9), (10, 10), (11, 11), (12, 12), (13, 13), (14, 14), (15, 15), (16, 16), (17, 17), (18, 18), (19, 19), (20, 20), (21, 21), (22, 22), (b'X', b'X'), (b'Y', b'Y'), (b'M', b'M')])),
                ('pos', models.IntegerField(null=True, blank=True)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='snp',
            unique_together=set([('snp_id_current', 'population')]),
        ),
    ]
