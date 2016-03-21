# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('genome', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PopulationPcaGeoPoint',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('src', models.CharField(max_length=128)),
                ('pc_1', models.FloatField(null=True)),
                ('pc_2', models.FloatField(null=True)),
                ('population_code', models.CharField(max_length=16, null=True, blank=True)),
                ('genome', models.ForeignKey(to='genome.Genome', null=True)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='populationpcageopoint',
            unique_together=set([('src', 'genome')]),
        ),
        migrations.AlterIndexTogether(
            name='populationpcageopoint',
            index_together=set([('src', 'population_code', 'genome')]),
        ),
    ]
