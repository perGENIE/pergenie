# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('genome', '0001_initial'),
        ('gwascatalog', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PhenotypeRiskReport',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('estimated_risk', models.DecimalField(null=True, max_digits=5, decimal_places=4)),
                ('phenotype', models.ForeignKey(to='gwascatalog.GwasCatalogPhenotype')),
            ],
        ),
        migrations.CreateModel(
            name='RiskReport',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('display_id', models.CharField(unique=True, max_length=8)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('genome', models.ForeignKey(to='genome.Genome')),
            ],
        ),
        migrations.CreateModel(
            name='SnpRiskReport',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('estimated_risk', models.DecimalField(null=True, max_digits=5, decimal_places=4)),
                ('evidence_snp', models.ForeignKey(to='gwascatalog.GwasCatalogSnp')),
                ('phenotype_risk_report', models.ForeignKey(to='riskreport.PhenotypeRiskReport')),
            ],
        ),
        migrations.AddField(
            model_name='phenotyperiskreport',
            name='risk_report',
            field=models.ForeignKey(to='riskreport.RiskReport'),
        ),
        migrations.AlterUniqueTogether(
            name='snpriskreport',
            unique_together=set([('phenotype_risk_report', 'evidence_snp')]),
        ),
        migrations.AlterUniqueTogether(
            name='phenotyperiskreport',
            unique_together=set([('risk_report', 'phenotype')]),
        ),
    ]
