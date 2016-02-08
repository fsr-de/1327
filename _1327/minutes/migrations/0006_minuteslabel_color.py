# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('minutes', '0005_auto_20160120_1758'),
    ]

    operations = [
        migrations.AddField(
            model_name='minuteslabel',
            name='color',
            field=models.CharField(default='#337ab7', max_length=7),
            preserve_default=False,
        ),
    ]
