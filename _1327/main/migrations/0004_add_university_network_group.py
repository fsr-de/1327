# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
from django.contrib.auth.models import Group


def add_university_network_group(apps, schema_editor):
	Group.objects.create(name="University Network")


class Migration(migrations.Migration):

	dependencies = [
		('main', '0003_menu_item_data'),
	]

	operations = [
		migrations.RunPython(add_university_network_group),
	]
