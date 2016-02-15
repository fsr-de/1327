# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

	dependencies = [
		('main', '0006_footer'),
	]

	operations = [
		migrations.AddField(
			model_name='menuitem',
			name='menu_type',
			field=models.IntegerField(default=1, choices=[(1, 'Main Menu'), (2, 'Footer')]),
		),
	]
