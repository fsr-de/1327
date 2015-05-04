# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0006_merge'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='initial',
            field=models.BooleanField(default=True),
            preserve_default=True,
        ),
    ]
