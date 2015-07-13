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
            name='Choice',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('text', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, default='')),
                ('votes', models.IntegerField(default=0)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Poll',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, default='')),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('is_multiple_choice_question', models.BooleanField(default=True)),
                ('participants', models.ManyToManyField(related_name='polls', blank=True, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'permissions': (('view_poll', 'User/Group is allowed to view that question'),),
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='choice',
            name='poll',
            field=models.ForeignKey(related_name='choices', to='polls.Poll'),
            preserve_default=True,
        ),
    ]
