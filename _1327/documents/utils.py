import json

from django.db import transaction
import reversion

from _1327.documents.models import TemporaryDocumentText
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


def handle_autosave(request, document):
	context = RequestContext(request)
	if request.method == 'POST':
		form = TextForm(request.POST)
		text_strip = request.POST['text'].strip()
		if text_strip != '':
			cleaned_data = form.cleaned_data

			if document is None:
				temporary_document_text = TemporaryDocumentText()
			elif document.text != cleaned_data['text']:
				temporary_document_text, created = TemporaryDocumentText.objects.get_or_create(document=document)
				temporary_document_text.document = document
			else:
				return

			temporary_document_text.text = cleaned_data['text']
			temporary_document_text.save()

def prepare_versions(document):
	versions = reversion.get_for_object(document).reverse()

	# prepare data for the template
	version_list = []
	for id, version in enumerate(versions):
		version_list.append((id, version, json.dumps(version.field_dict['text']).strip('"')))

	return version_list
