# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def initial_data(apps, schema_editor):
	# We can't import the MenuItem model directly as it may be a newer
	# version than this migration expects. We use the historical version.
	# We can't import the MenuItem model directly as it may be a newer
	# version than this migration expects. We use the historical version.
	MenuItem = apps.get_model("main", "MenuItem")

	MenuItem.objects.all().delete()

	menu_item = MenuItem()
	menu_item.title = "Main Page"
	menu_item.link = 'index'
	menu_item.order = 1
	menu_item.menu_type = 1  # MenuItem.MAIN_MENU
	menu_item.save()

	menu_item = MenuItem()
	menu_item.title = "Minutes"
	menu_item.link = 'minutes:list'
	menu_item.order = 2
	menu_item.menu_type = 1  # MenuItem.MAIN_MENU
	menu_item.save()

	menu_item = MenuItem()
	menu_item.title = "Admin"
	menu_item.link = 'admin:index'
	menu_item.order = 1
	menu_item.menu_type = 2  # MenuItem.FOOTER
	menu_item.save()


def delete_menu_data(apps, schema_editor):
	MenuItem = apps.get_model("main", "MenuItem")

	for item in MenuItem.objects.all():
		item.delete()


class Migration(migrations.Migration):
	dependencies = [
		('main', '0002_add_staff_group'),
	]


	operations = [
		migrations.RunPython(initial_data, delete_menu_data),
	]
