import json

from django.db import transaction
from django.template import RequestContext
import reversion

from _1327.documents.models import Document, TemporaryDocumentText
from _1327.documents.forms import TextForm


class FormValidException(Exception):
	pass


def handle_edit(request, document):
	context = RequestContext(request)
	if request.method == 'POST':
		form = TextForm(request.POST)
		if form.is_valid():
			cleaned_data = form.cleaned_data

			document.text = cleaned_data['text']
			document.type = cleaned_data['type']
			document.author = request.user
			if document.title != cleaned_data['title']:
				# if the user changed the title we have to delete the old version
				# because the url_title will change, too...
				document.title = cleaned_data['title']
				new_document = Document(title=document.title,
										text=document.text,
										type=document.type,
										author=document.author, )
				document.delete()
				document = new_document

			# save the document and also save the user and the comment the user added
			with transaction.atomic(), reversion.create_revision():
				document.save()
				reversion.set_user(request.user)
				reversion.set_comment(cleaned_data['comment'])
			raise FormValidException
		else:
			context['errors'] = form.errors
			context['form'] = form
	else:
		form_data = {
			'title': document.title,
			'text': document.text,
			'type': document.type,
		}
		context['form'] = TextForm(form_data)

	context['document'] = document
	return context

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

def prepare_versions(request, document):
	context = RequestContext(request)
	versions = reversion.get_for_object(document).reverse()

	# prepare data for the template
	version_list = []
	for id, version in enumerate(versions):
		version_list.append((id, version, json.dumps(version.field_dict['text']).strip('"')))

	context['document'] = document
	context['versions'] = version_list
	context['url_title'] = document.url_title

	return context
