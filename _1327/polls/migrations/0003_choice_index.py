# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0002_auto_20150720_1906'),
    ]

    operations = [
        migrations.AddField(
            model_name='choice',
            name='index',
            field=models.IntegerField(verbose_name='ordering index', default=0),
        ),
    ]
