# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.utils.timezone import utc
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0002_auto_20141101_2244'),
    ]

    operations = [
        migrations.CreateModel(
            name='TemporaryDocumentText',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('text', models.TextField()),
                ('document', models.ForeignKey(to='documents.Document', related_name='document')),
                ('created', models.DateTimeField(default=datetime.datetime(2015, 2, 16, 19, 12, 14, 661384, tzinfo=utc), auto_now=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
