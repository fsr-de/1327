# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('documents', '0009_auto_20150509_1711'),
    ]

    operations = [
        migrations.CreateModel(
            name='MinutesDocument',
            fields=[
                ('document_ptr', models.OneToOneField(parent_link=True, to='documents.Document', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField(verbose_name='Date', default=datetime.datetime.now)),
                ('state', models.IntegerField(choices=[(0, 'Unpublished'), (1, 'Published'), (2, 'Internal')], verbose_name='State', default=0)),
                ('moderator', models.ForeignKey(to=settings.AUTH_USER_MODEL, verbose_name='Moderator', related_name='moderations')),
                ('participants', models.ManyToManyField(verbose_name='Participants', to=settings.AUTH_USER_MODEL, related_name='participations')),
            ],
            options={
                'verbose_name': 'Minutes',
                'verbose_name_plural': 'Minutes',
                'permissions': (('view_minutesdocument', 'User/Group is allowed to view those minutes'),),
                'abstract': False,
            },
            bases=('documents.document',),
        ),
    ]
