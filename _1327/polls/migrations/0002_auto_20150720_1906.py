# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='poll',
            name='is_multiple_choice_question',
        ),
        migrations.AddField(
            model_name='poll',
            name='max_allowed_number_of_answers',
            field=models.IntegerField(default=1),
        ),
    ]
