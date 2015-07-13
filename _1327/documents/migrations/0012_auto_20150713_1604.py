# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0011_auto_20150518_1829'),
    ]

    operations = [
        migrations.AddField(
            model_name='attachment',
            name='index',
            field=models.IntegerField(default=0, verbose_name='ordering index'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='document',
            name='polymorphic_ctype',
            field=models.ForeignKey(editable=False, to='contenttypes.ContentType', related_name='polymorphic_documents.document_set', null=True),
            preserve_default=True,
        ),
    ]
