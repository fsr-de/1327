# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
from guardian.management import create_anonymous_user
from guardian.utils import get_anonymous_user
from guardian.conf import settings as guardian_settings

from _1327.user_management.models import UserProfile


def add_anonymous_group(apps, schema_editor):
	User = apps.get_model("user_management", "UserProfile")
	user_arguments = {UserProfile.USERNAME_FIELD: guardian_settings.ANONYMOUS_USER_NAME}
	anonymous_user = User(**user_arguments)
	# anonymous_user.set_unusable_password()
	anonymous_user.save()

	# create_anonymous_user(None)
	Group = apps.get_model("auth", "Group")
	group = Group.objects.create(name="Anonymous")
	# user = get_anonymous_user()
	# user.groups.add(group)
	anonymous_user.groups.add(group)

class Migration(migrations.Migration):

	dependencies = [
		('main', '0004_add_university_network_group'),
	]

	operations = [
		migrations.RunPython(add_anonymous_group),
	]
