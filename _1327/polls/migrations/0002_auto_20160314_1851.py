# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('polls', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='poll',
            name='participants',
            field=models.ManyToManyField(related_name='polls', blank=True, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='choice',
            name='poll',
            field=models.ForeignKey(related_name='choices', to='polls.Poll', on_delete=models.deletion.CASCADE),
        ),
    ]
