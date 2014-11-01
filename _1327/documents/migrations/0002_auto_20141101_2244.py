# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='document',
            name='type',
            field=models.CharField(max_length=5, default='I'),
        ),
    ]
