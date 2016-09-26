# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
from django.contrib.auth.models import Group


def add_student_group(apps, schema_editor):
	Group.objects.create(name="Student")

def remove_student_group(apps, schema_editor):
	Group.objects.get(name="Student").delete()

class Migration(migrations.Migration):

	dependencies = [
		('main', '0010_menu_item_minutes'),
	]

	operations = [
		migrations.RunPython(add_student_group, remove_student_group),
	]
