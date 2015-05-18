# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0009_auto_20150509_1711'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='document',
            name='initial',
        ),
    ]
