# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0004_auto_20160118_1953'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='poll',
            options={'permissions': (('view_poll', 'User/Group is allowed to view that poll'),)},
        ),
    ]
