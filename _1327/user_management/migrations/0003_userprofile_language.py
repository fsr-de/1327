# -*- coding: utf-8 -*-
# Generated by Django 1.11.14 on 2018-07-23 17:24
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

	dependencies = [
		('user_management', '0002_auto_20170306_1738'),
	]
	operations = [
		migrations.AddField(
			model_name='userprofile',
			name='language',
			field=models.CharField(blank=True, max_length=8, null=True, verbose_name='language'),
		),
	]
