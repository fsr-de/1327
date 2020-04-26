from django.db import migrations


class Migration(migrations.Migration):

	dependencies = [
		('main', '0014_add_on_delete'),
	]

	operations = [
		migrations.AlterModelOptions(
			name='menuitem',
			options={'ordering': ['order'], 'permissions': (('changechildren_menuitem', 'User/Group is allowed to change children items'),)},
		),
	]
