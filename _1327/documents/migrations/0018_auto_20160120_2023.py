# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0017_auto_20160118_1953'),
    ]

    operations = [
        migrations.AlterField(
            model_name='document',
            name='created',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
