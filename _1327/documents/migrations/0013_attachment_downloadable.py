# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0012_auto_20150713_1604'),
    ]

    operations = [
        migrations.AddField(
            model_name='attachment',
            name='downloadable',
            field=models.BooleanField(default=True, verbose_name='Can be downloaded'),
            preserve_default=True,
        ),
    ]
