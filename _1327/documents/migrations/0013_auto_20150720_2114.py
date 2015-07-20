# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0012_auto_20150713_1604'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='document',
            name='author',
        ),
        migrations.AlterField(
            model_name='document',
            name='polymorphic_ctype',
            field=models.ForeignKey(editable=False, to='contenttypes.ContentType', null=True, related_name='polymorphic_documents.document_set+'),
        ),
    ]
