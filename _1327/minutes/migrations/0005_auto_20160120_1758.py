# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('minutes', '0004_guest'),
    ]

    operations = [
        migrations.AlterField(
            model_name='minutesdocument',
            name='moderator',
            field=models.ForeignKey(null=True, verbose_name='Moderator', to=settings.AUTH_USER_MODEL, blank=True, related_name='moderations'),
        ),
    ]
