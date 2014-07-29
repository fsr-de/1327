# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MenuItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('title', models.CharField(verbose_name='Title', max_length=255)),
                ('order', models.IntegerField()),
                ('link', models.CharField(verbose_name='Link', max_length=255, blank=True, null=True)),
                ('document', models.ForeignKey(verbose_name='Document', to='documents.Document', blank=True, null=True)),
                ('parent', models.ForeignKey(to='main.MenuItem', related_name='children', blank=True, null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
