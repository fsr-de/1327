# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0006_merge'),
    ]

    operations = [
        migrations.CreateModel(
            name='Attachment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now=True)),
                ('file', models.FileField(upload_to='documents/%y/%m/')),
                ('document', models.ForeignKey(related_name='attachments', to='documents.Document')),
                ('displayname', models.TextField(max_length=255, blank=True, default='')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
