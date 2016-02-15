# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import _1327.minutes.fields


class Migration(migrations.Migration):

    dependencies = [
        ('minutes', '0007_auto_20160208_2122'),
    ]

    operations = [
        migrations.AlterField(
            model_name='minuteslabel',
            name='color',
            field=_1327.minutes.fields.HexColorModelField(max_length=7),
        ),
    ]
