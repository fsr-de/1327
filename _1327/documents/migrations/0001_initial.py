# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Attachment',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('displayname', models.TextField(verbose_name='Display name', default='', blank=True, max_length=255)),
                ('created', models.DateTimeField(auto_now=True, verbose_name='Created')),
                ('file', models.FileField(upload_to='documents/%y/%m/', verbose_name='File')),
                ('index', models.IntegerField(verbose_name='ordering index', default=0)),
                ('no_direct_download', models.BooleanField(verbose_name='Do not show as attachment (for embedded images)', default=False)),
            ],
            options={
                'verbose_name_plural': 'Attachments',
                'verbose_name': 'Attachment',
            },
        ),
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('title', models.CharField(max_length=255)),
                ('url_title', models.SlugField()),
                ('text', models.TextField()),
            ],
            options={
                'verbose_name_plural': 'Documents',
                'verbose_name': 'Document',
                'permissions': (('view_document', 'User/Group is allowed to view that document'),),
            },
        ),
        migrations.CreateModel(
            name='TemporaryDocumentText',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField()),
                ('created', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
