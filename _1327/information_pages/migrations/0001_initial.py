# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='InformationDocument',
            fields=[
                ('document_ptr', models.OneToOneField(primary_key=True, auto_created=True, to='documents.Document', serialize=False, parent_link=True, on_delete=models.deletion.CASCADE)),
            ],
            options={
                'verbose_name_plural': 'Information documents',
                'verbose_name': 'Information document',
                'abstract': False,
                'permissions': (('view_informationdocument', 'User/Group is allowed to view that document'),),
            },
            bases=('documents.document',),
        ),
    ]
