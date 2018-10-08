# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
from guardian.management import create_anonymous_user
from guardian.utils import get_anonymous_user

def add_anonymous_group(apps, schema_editor):
	create_anonymous_user(None)
	Group = apps.get_model("auth", "Group")
	group = Group.objects.create(name="Anonymous")
	user = get_anonymous_user()
	user.groups.add(group)

class Migration(migrations.Migration):

	dependencies = [
		('main', '0004_add_university_network_group'),
		('user_management', '0003_userprofile_language'),
	]

	operations = [
		migrations.RunPython(add_anonymous_group),
	]
