# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0015_merge'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='attachment',
            name='downloadable',
        ),
        migrations.AddField(
            model_name='attachment',
            name='no_direct_download',
            field=models.BooleanField(default=False, verbose_name='Do not allow direct download as attachment (used for embedded images)'),
        ),
    ]
