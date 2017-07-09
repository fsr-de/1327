# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime
import _1327.minutes.fields


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Guest',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Name')),
            ],
        ),
        migrations.CreateModel(
            name='MinutesDocument',
            fields=[
                ('document_ptr', models.OneToOneField(primary_key=True, auto_created=True, to='documents.Document', serialize=False, parent_link=True, on_delete=models.deletion.CASCADE)),
                ('date', models.DateField(verbose_name='Date', default=datetime.datetime.now)),
                ('state', models.IntegerField(verbose_name='State', default=0, choices=[(0, 'Unpublished'), (1, 'Published'), (2, 'Internal')])),
            ],
            options={
                'verbose_name_plural': 'Minutes',
                'verbose_name': 'Minutes',
                'abstract': False,
                'permissions': (('view_minutesdocument', 'User/Group is allowed to view those minutes'),),
            },
            bases=('documents.document',),
        ),
        migrations.CreateModel(
            name='MinutesLabel',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('color', _1327.minutes.fields.HexColorModelField(max_length=7)),
            ],
        ),
    ]
