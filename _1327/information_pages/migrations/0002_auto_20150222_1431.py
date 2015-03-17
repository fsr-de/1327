# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0005_auto_20150222_1431'),
        ('information_pages', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='InformationDocument',
            fields=[
                ('document_ptr', models.OneToOneField(primary_key=True, parent_link=True, auto_created=True, serialize=False, to='documents.Document')),
            ],
            options={
                'abstract': False,
            },
            bases=('documents.document',),
        ),
        migrations.RemoveField(
            model_name='document',
            name='author',
        ),
        migrations.DeleteModel(
            name='Document',
        ),
    ]
