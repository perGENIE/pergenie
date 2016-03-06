# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
import django.contrib.postgres.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='GwasCatalogPhenotype',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=1024)),
            ],
        ),
        migrations.CreateModel(
            name='GwasCatalogSnp',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('is_active', models.BooleanField(default=False)),
                ('date_downloaded', models.DateTimeField()),
                ('pubmed_id', models.CharField(max_length=8)),
                ('date_published', models.DateTimeField(null=True)),
                ('study_title', models.CharField(default=b'', max_length=1024, blank=True)),
                ('pubmed_url', models.CharField(default=b'', max_length=1024, blank=True)),
                ('disease_or_trait', models.CharField(default=b'', max_length=1024, blank=True)),
                ('snp_id_reported', models.IntegerField(null=True)),
                ('snp_id_current', models.IntegerField(null=True)),
                ('risk_allele', models.CharField(default=b'', max_length=1024, blank=True)),
                ('risk_allele_forward', models.CharField(default=b'', max_length=1024, blank=True)),
                ('initial_sample', models.CharField(max_length=1024, blank=True)),
                ('chrom_reported', models.CharField(max_length=2, blank=True)),
                ('pos_reported', models.IntegerField(null=True)),
                ('gene_reported', models.CharField(default=b'', max_length=1024, blank=True)),
                ('risk_allele_freq_reported', models.DecimalField(null=True, max_digits=5, decimal_places=4)),
                ('p_value', models.DecimalField(null=True, max_digits=1000, decimal_places=1000)),
                ('p_value_text', models.CharField(default=b'', max_length=1024, blank=True)),
                ('odds_ratio_or_beta_coeff', models.DecimalField(null=True, max_digits=10, decimal_places=5)),
                ('confidence_interval_95_percent', models.CharField(default=b'', max_length=1024, blank=True)),
                ('reliability_rank', models.FloatField(null=True)),
                ('population', django.contrib.postgres.fields.ArrayField(default=[], base_field=models.CharField(max_length=1024, blank=True), size=None)),
                ('odds_ratio', models.DecimalField(null=True, max_digits=10, decimal_places=5)),
                ('beta_coeff', models.DecimalField(null=True, max_digits=10, decimal_places=5)),
                ('beta_coeff_unit', models.CharField(default=b'', max_length=1024, blank=True)),
                ('phenotype', models.ForeignKey(to='gwascatalog.GwasCatalogPhenotype')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='gwascatalogsnp',
            unique_together=set([('date_downloaded', 'pubmed_id', 'phenotype', 'snp_id_current', 'risk_allele')]),
        ),
    ]
