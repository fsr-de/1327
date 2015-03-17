# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0003_temporarydocumenttext'),
    ]

    operations = [
        migrations.AlterField(
            model_name='temporarydocumenttext',
            name='created',
            field=models.DateTimeField(auto_now=True),
            preserve_default=True,
        ),
    ]
