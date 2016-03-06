# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gwascatalog', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='gwascatalogsnp',
            name='first_author',
            field=models.CharField(default=b'', max_length=1024, blank=True),
        ),
        migrations.AddField(
            model_name='gwascatalogsnp',
            name='journal',
            field=models.CharField(default=b'', max_length=1024, blank=True),
        ),
    ]
