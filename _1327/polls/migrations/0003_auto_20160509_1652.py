# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0002_auto_20160321_1755'),
        ('polls', '0002_auto_20160314_1851'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='poll',
            name='description',
        ),
        migrations.RemoveField(
            model_name='poll',
            name='id',
        ),
        migrations.RemoveField(
            model_name='poll',
            name='title',
        ),
        migrations.AddField(
            model_name='poll',
            name='document_ptr',
            field=models.OneToOneField(to='documents.Document', primary_key=True, serialize=False, parent_link=True, default=0, auto_created=True, on_delete=models.deletion.CASCADE),
            preserve_default=False,
        ),
    ]
