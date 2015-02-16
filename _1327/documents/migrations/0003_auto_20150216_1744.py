# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0002_auto_20141101_2244'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='document',
            options={'permissions': (('view_document', 'User/Group is allowed to View that Document'),)},
        ),
    ]
