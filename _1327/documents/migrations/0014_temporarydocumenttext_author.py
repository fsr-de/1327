# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('documents', '0013_auto_20150720_2114'),
    ]

    operations = [
        migrations.AddField(
            model_name='temporarydocumenttext',
            name='author',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='temporary_documents', default=1),
            preserve_default=False,
        ),
    ]
