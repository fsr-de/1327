# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0003_auto_20160509_1652'),
    ]

    operations = [
        migrations.AlterField(
            model_name='poll',
            name='end_date',
            field=models.DateField(default=datetime.datetime.now, verbose_name='End Date'),
        ),
        migrations.AlterField(
            model_name='poll',
            name='start_date',
            field=models.DateField(default=datetime.datetime.now, verbose_name='Start Date'),
        ),
    ]
