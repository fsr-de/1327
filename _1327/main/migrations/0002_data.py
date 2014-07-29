# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def initial_data(apps, schema_editor):
	# We can't import the MenuItem model directly as it may be a newer
	# version than this migration expects. We use the historical version.
	MenuItem = apps.get_model("main", "MenuItem")

	menu_item = MenuItem()
	menu_item.title = "Main Page"
	menu_item.link = '_1327.main.views.index'
	menu_item.order = 1
	menu_item.save()

	menu_item = MenuItem()
	menu_item.title = "Admin"
	menu_item.link = 'admin:index'
	menu_item.order = 2
	menu_item.save()


class Migration(migrations.Migration):
	dependencies = [
		('main', '0001_initial'),
	]

	operations = [
		migrations.RunPython(initial_data),
	]
