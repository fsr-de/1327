# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('information_pages', '0002_auto_20150222_1431'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='informationdocument',
            options={'permissions': (('view_informationdocument', 'User/Group is allowed to view that information'),)},
        ),
    ]
