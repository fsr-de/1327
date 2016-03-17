# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0005_auto_20160216_2149'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='poll',
            options={'permissions': (('view_poll', 'User/Group is allowed to view that poll'), ('vote_poll', 'User/Group is allowed to participate (vote) in that poll'))},
        ),
    ]
