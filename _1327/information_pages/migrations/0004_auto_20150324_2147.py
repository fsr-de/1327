# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('information_pages', '0003_auto_20150317_1839'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='informationdocument',
            options={'permissions': (('view_informationdocument', 'User/Group is allowed to view that document'),)},
        ),
    ]
