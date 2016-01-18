# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0016_auto_20151123_1929'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attachment',
            name='no_direct_download',
            field=models.BooleanField(default=False, verbose_name='Do not show as attachment (for embedded images)'),
        ),
    ]
