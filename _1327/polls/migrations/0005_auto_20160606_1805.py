# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0004_auto_20160530_1932'),
    ]

    operations = [
        migrations.AlterField(
            model_name='poll',
            name='max_allowed_number_of_answers',
            field=models.PositiveIntegerField(default=1),
        ),
    ]
