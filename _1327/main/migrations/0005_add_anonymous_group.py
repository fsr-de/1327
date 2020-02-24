# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.hashers import make_password
from django.db import migrations
from guardian.conf import settings as guardian_settings

from _1327.user_management.models import UserProfile


def add_anonymous_group(apps, schema_editor):
	User = apps.get_model("user_management", "UserProfile")
	user_arguments = {UserProfile.USERNAME_FIELD: guardian_settings.ANONYMOUS_USER_NAME}
	anonymous_user = User(**user_arguments)
	anonymous_user.password = make_password(None)
	anonymous_user.save()

	Group = apps.get_model("auth", "Group")
	group = Group.objects.create(name="Anonymous")
	anonymous_user.groups.add(group)


class Migration(migrations.Migration):
	dependencies = [
		('main', '0004_add_university_network_group'),
	]

	operations = [
		migrations.RunPython(add_anonymous_group),
	]
