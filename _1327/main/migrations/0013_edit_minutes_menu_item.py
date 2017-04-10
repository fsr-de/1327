# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def adapt_links(MenuItem, old_link, new_link, split_str='?'):
	menu_items = MenuItem.objects.filter(link__contains=old_link).all()

	for menu_item in menu_items:
		id = menu_item.link.split(split_str)[-1]
		menu_item.link = '{}{}'.format(new_link, id)
		menu_item.save()


def adapt_minutes_link(apps, schema_editor):
	# We can't import the MenuItem model directly as it may be a newer
	# version than this migration expects. We use the historical version.
	MenuItem = apps.get_model("main", "MenuItem")

	adapt_links(MenuItem, 'minutes:list?', 'minutes:list?groupid=')


def reverse_minutes_link_adaption(apps, schema_editor):
	MenuItem = apps.get_model("main", "MenuItem")

	adapt_links(MenuItem, 'minutes:list?groupid=', 'minutes:list?', split_str='?groupid=')


class Migration(migrations.Migration):
	dependencies = [
		('main', '0012_auto_20161029_2223'),
	]

	operations = [
		migrations.RunPython(adapt_minutes_link, reverse_minutes_link_adaption),
	]
