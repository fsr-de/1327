# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.utils.timezone import utc
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0003_temporarydocumenttext'),
    ]

    operations = [
        migrations.AddField(
            model_name='temporarydocumenttext',
            name='created',
            field=models.DateTimeField(default=datetime.datetime(2015, 2, 16, 19, 12, 14, 661384, tzinfo=utc), auto_now=True),
            preserve_default=False,
        ),
    ]
