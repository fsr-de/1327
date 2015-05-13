# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user_management', '0003_auto_20150508_1210'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userprofile',
            name='is_admin',
        ),
    ]
