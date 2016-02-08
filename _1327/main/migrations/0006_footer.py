# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def initial_data(apps, schema_editor):
	# We can't import the MenuItem model directly as it may be a newer
	# version than this migration expects. We use the historical version.
	MenuItem = apps.get_model("main", "MenuItem")

	for item in MenuItem.objects.all():
		item.delete()

	main_menu = MenuItem()
	main_menu.title = "Main Menu"
	main_menu.order = 0
	main_menu.save()

	footer = MenuItem()
	footer.title = "Footer"
	footer.order = 0
	footer.save()

	menu_item = MenuItem()
	menu_item.title = "Main Page"
	menu_item.link = '_1327.main.views.index'
	menu_item.parent = main_menu
	menu_item.order = 1
	menu_item.save()

	menu_item = MenuItem()
	menu_item.title = "Admin"
	menu_item.link = 'admin:index'
	menu_item.parent = footer
	menu_item.order = 1
	menu_item.save()


def delete_menu_data(apps, schema_editor):
	MenuItem = apps.get_model("main", "MenuItem")

	for item in MenuItem.objects.all():
		item.delete()


class Migration(migrations.Migration):
	dependencies = [
		('main', '0005_add_staff_group'),
	]


	operations = [
		migrations.RunPython(initial_data, delete_menu_data),
	]
