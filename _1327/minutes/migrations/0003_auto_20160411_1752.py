# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('minutes', '0002_auto_20160321_1755'),
    ]

    operations = [
        migrations.AlterField(
            model_name='minutesdocument',
            name='state',
            field=models.IntegerField(verbose_name='State', default=0, choices=[(0, 'Unpublished'), (1, 'Published'), (2, 'Internal'), (3, 'Custom')]),
        ),
    ]
