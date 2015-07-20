# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('minutes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MinutesLabel',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('minutes', models.ManyToManyField(blank=True, related_name='labels', to='minutes.MinutesDocument')),
            ],
        ),
    ]
