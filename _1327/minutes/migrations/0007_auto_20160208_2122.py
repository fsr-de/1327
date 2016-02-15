# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('minutes', '0006_minuteslabel_color'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='minuteslabel',
            name='minutes',
        ),
        migrations.AddField(
            model_name='minutesdocument',
            name='labels',
            field=models.ManyToManyField(related_name='minutes', to='minutes.MinutesLabel', blank=True),
        ),
    ]
