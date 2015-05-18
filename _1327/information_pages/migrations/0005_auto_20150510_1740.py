# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('information_pages', '0004_auto_20150324_2147'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='informationdocument',
            options={'verbose_name_plural': 'Information documents', 'verbose_name': 'Information document', 'permissions': (('view_informationdocument', 'User/Group is allowed to view that document'),)},
        ),
    ]
