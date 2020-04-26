from django.db import migrations


class Migration(migrations.Migration):

	dependencies = [
		('minutes', '0011_auto_20180825_1121'),
	]

	operations = [
		migrations.AlterModelOptions(
			name='minutesdocument',
			options={'base_manager_name': 'objects', 'verbose_name': 'Minutes', 'verbose_name_plural': 'Minutes'},
		),
	]
