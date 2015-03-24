# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_data'),
    ]

    operations = [
        migrations.AddField(
            model_name='menuitem',
            name='staff_only',
            field=models.BooleanField(default=False, verbose_name='Display for staff only'),
            preserve_default=True,
        ),
    ]
