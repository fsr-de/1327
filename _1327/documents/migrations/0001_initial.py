# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('title', models.CharField(max_length=255)),
                ('url_title', models.SlugField()),
                ('text', models.TextField()),
                ('type', models.IntegerField(default=1)),
                ('author', models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='documents')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
