# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def add_student_group(apps, schema_editor):
	Group = apps.get_model("auth", "Group")
	Group.objects.create(name="Student")

def remove_student_group(apps, schema_editor):
	Group = apps.get_model("auth", "Group")
	Group.objects.get(name="Student").delete()

class Migration(migrations.Migration):

	dependencies = [
		('main', '0010_menu_item_minutes'),
	]

	operations = [
		migrations.RunPython(add_student_group, remove_student_group),
	]
