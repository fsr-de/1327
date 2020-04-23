from django.db import migrations


class Migration(migrations.Migration):

	dependencies = [
		('documents', '0010_add_on_delete'),
	]

	operations = [
		migrations.AlterModelOptions(
			name='document',
			options={'verbose_name': 'Document', 'verbose_name_plural': 'Documents'},
		),
	]
