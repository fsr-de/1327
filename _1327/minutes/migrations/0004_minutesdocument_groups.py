# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
        ('minutes', '0003_auto_20160411_1752'),
    ]

    operations = [
        migrations.AddField(
            model_name='minutesdocument',
            name='groups',
            field=models.ManyToManyField(related_name='minutes', blank=True, to='auth.Group'),
        ),
    ]
