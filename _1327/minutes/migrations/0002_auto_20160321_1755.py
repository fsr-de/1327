# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('minutes', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='minutesdocument',
            name='author',
            field=models.ForeignKey(related_name='documents', to=settings.AUTH_USER_MODEL, on_delete=models.deletion.PROTECT),
        ),
        migrations.AddField(
            model_name='minutesdocument',
            name='labels',
            field=models.ManyToManyField(related_name='minutes', to='minutes.MinutesLabel', blank=True),
        ),
        migrations.AddField(
            model_name='minutesdocument',
            name='moderator',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True, verbose_name='Moderator', related_name='moderations', blank=True, on_delete=models.deletion.PROTECT),
        ),
        migrations.AddField(
            model_name='minutesdocument',
            name='participants',
            field=models.ManyToManyField(related_name='participations', to=settings.AUTH_USER_MODEL, verbose_name='Participants'),
        ),
        migrations.AddField(
            model_name='guest',
            name='minute',
            field=models.ForeignKey(to='minutes.MinutesDocument', verbose_name='Guests', related_name='guests', on_delete=models.deletion.CASCADE),
        ),
    ]
