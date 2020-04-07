from django.db import migrations


class Migration(migrations.Migration):

	dependencies = [
		('information_pages', '0005_auto_20180825_1121'),
	]

	operations = [
		migrations.AlterModelOptions(
			name='informationdocument',
			options={'base_manager_name': 'objects', 'verbose_name': 'Information document', 'verbose_name_plural': 'Information documents'},
		),
	]
