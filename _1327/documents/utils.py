import json

from django.db import transaction
import reversion

from .forms import TextForm


def handle_edit(request, document):
	if request.method == 'POST':
		form = TextForm(request.POST)
		if form.is_valid():
			cleaned_data = form.cleaned_data

			document.title = cleaned_data['title']
			document.text = cleaned_data['text']
			document.type = cleaned_data['type']
			document.author = request.user

			# save the document and also save the user and the comment the user added
			with transaction.atomic(), reversion.create_revision():
				document.save()
				reversion.set_user(request.user)
				reversion.set_comment(cleaned_data['comment'])
			return True, form
	else:
		form_data = {
			'title': document.title,
			'text': document.text,
			'type': document.type,
		}
		form = TextForm(form_data)
	return False, form


def prepare_versions(document):
	versions = reversion.get_for_object(document).reverse()

	# prepare data for the template
	version_list = []
	for id, version in enumerate(versions):
		version_list.append((id, version, json.dumps(version.field_dict['text']).strip('"')))

	return version_list
