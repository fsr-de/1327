# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Choice',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('text', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, default='')),
                ('votes', models.IntegerField(default=0)),
                ('index', models.IntegerField(verbose_name='ordering index', default=0)),
            ],
            options={
                'ordering': ['index'],
            },
        ),
        migrations.CreateModel(
            name='Poll',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, default='')),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('max_allowed_number_of_answers', models.IntegerField(default=1)),
            ],
            options={
                'permissions': (('view_poll', 'User/Group is allowed to view that poll'), ('vote_poll', 'User/Group is allowed to participate (vote) in that poll')),
            },
        ),
    ]
