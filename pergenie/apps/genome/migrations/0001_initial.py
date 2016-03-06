# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.contrib.postgres.fields
import django.utils.timezone
from django.conf import settings
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Genome',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('file_name', models.FilePathField()),
                ('display_name', models.CharField(max_length=100)),
                ('file_format', models.CharField(default=b'VCF', max_length=5, choices=[(b'VCF', b'VCF')])),
                ('population', models.CharField(default=b'UN', max_length=3, choices=[(b'UN', 'Unknown'), (b'EAS', 'EastAsian'), (b'EUR', 'European'), (b'AFR', 'African')])),
                ('gender', models.CharField(default=b'U', max_length=1, choices=[(b'U', 'Unknown'), (b'M', 'Male'), (b'F', 'Female')])),
                ('status', models.IntegerField(default=0)),
                ('error', models.CharField(max_length=256, null=True, blank=True)),
                ('owner', models.ForeignKey(related_name='owner', to=settings.AUTH_USER_MODEL)),
                ('readers', models.ManyToManyField(related_name='reader', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Genotype',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('rs_id_current', models.IntegerField()),
                ('genotype', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=1024), size=2)),
                ('genome', models.ForeignKey(to='genome.Genome')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='genome',
            unique_together=set([('owner', 'display_name')]),
        ),
    ]
