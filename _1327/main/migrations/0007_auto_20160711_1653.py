# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0006_merge'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='menuitem',
            options={'permissions': (('view_menuitem', 'User/Group is allowed to view this menu item'),), 'ordering': ['order']},
        ),
        migrations.RemoveField(
            model_name='menuitem',
            name='staff_only',
        ),
    ]
