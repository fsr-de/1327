# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0002_auto_20160321_1755'),
    ]

    operations = [
        migrations.AlterField(
            model_name='document',
            name='url_title',
            field=models.SlugField(unique=True),
        ),
    ]
