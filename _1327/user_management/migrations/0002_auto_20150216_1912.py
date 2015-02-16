# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user_management', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='email',
            field=models.EmailField(blank=True, verbose_name='Email address', null=True, max_length=255),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='first_name',
            field=models.CharField(blank=True, verbose_name='First name', null=True, max_length=255),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='last_name',
            field=models.CharField(blank=True, verbose_name='Last name', null=True, max_length=255),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='username',
            field=models.CharField(unique=True, verbose_name='User name', max_length=255),
            preserve_default=True,
        ),
    ]
