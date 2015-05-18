# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0010_remove_document_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='attachment',
            options={'verbose_name': 'Attachment', 'verbose_name_plural': 'Attachments'},
        ),
        migrations.AlterModelOptions(
            name='document',
            options={'verbose_name': 'Document', 'permissions': (('view_document', 'User/Group is allowed to view that document'),), 'verbose_name_plural': 'Documents'},
        ),
        migrations.AlterField(
            model_name='attachment',
            name='created',
            field=models.DateTimeField(verbose_name='Created', auto_now=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='attachment',
            name='displayname',
            field=models.TextField(verbose_name='Display name', default='', blank=True, max_length=255),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='attachment',
            name='document',
            field=models.ForeignKey(verbose_name='Document', related_name='attachments', to='documents.Document'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='attachment',
            name='file',
            field=models.FileField(verbose_name='File', upload_to='documents/%y/%m/'),
            preserve_default=True,
        ),
    ]
