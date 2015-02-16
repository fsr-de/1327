# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
        ('documents', '0004_merge'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='document',
            name='type',
        ),
        migrations.AddField(
            model_name='document',
            name='polymorphic_ctype',
            field=models.ForeignKey(editable=False, null=True, related_name='polymorphic_documents.document_set', to='contenttypes.ContentType'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='temporarydocumenttext',
            name='created',
            field=models.DateTimeField(auto_now=True),
            preserve_default=True,
        ),
    ]
