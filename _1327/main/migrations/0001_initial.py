# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MenuItem',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='Title')),
                ('order', models.IntegerField()),
                ('link', models.CharField(null=True, verbose_name='Link', blank=True, max_length=255)),
                ('staff_only', models.BooleanField(verbose_name='Display for staff only', default=False)),
                ('menu_type', models.IntegerField(choices=[(1, 'Main Menu'), (2, 'Footer')], default=1)),
                ('document', models.ForeignKey(to='documents.Document', null=True, verbose_name='Document', blank=True, on_delete=models.deletion.PROTECT)),
                ('parent', models.ForeignKey(to='main.MenuItem', null=True, related_name='children', blank=True, on_delete=models.deletion.CASCADE)),
            ],
            options={
                'ordering': ['order'],
            },
        ),
    ]
