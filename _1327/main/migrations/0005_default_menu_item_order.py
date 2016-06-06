# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0004_add_university_network_group'),
    ]

    operations = [
        migrations.AlterField(
            model_name='menuitem',
            name='order',
            field=models.IntegerField(default=999),
        ),
    ]
