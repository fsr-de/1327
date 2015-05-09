# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.utils.timezone import utc
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0008_merge'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='created',
            field=models.DateTimeField(default=datetime.datetime(2015, 1, 1, 0, 0, 0, 0, tzinfo=utc), auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='document',
            name='polymorphic_ctype',
            field=models.ForeignKey(editable=False, related_name='polymorphic_documents.document_set+', null=True, to='contenttypes.ContentType'),
            preserve_default=True,
        ),
    ]
