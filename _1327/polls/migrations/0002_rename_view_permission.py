from django.db import migrations


class Migration(migrations.Migration):

	dependencies = [
		('polls', '0001_squashed_0006_initial'),
	]

	operations = [
		migrations.AlterModelOptions(
			name='poll',
			options={'permissions': (('vote_poll', 'User/Group is allowed to participate (vote) in that poll'),)},
		),
	]
