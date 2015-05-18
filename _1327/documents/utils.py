import json
import re

from django.db import transaction
import reversion

from _1327.documents.models import TemporaryDocumentText
from _1327.documents.forms import TextForm, AttachmentForm

def get_new_autosaved_pages_for_user(user):
	autosaved_pages = []
	all_temp_documents = TemporaryDocumentText.objects.all()
	for temp_document in all_temp_documents:
		document = temp_document.document
		if len(reversion.get_for_object(document)) == 0 and document.author == user:
			autosaved_pages.append(document)
	return autosaved_pages

def handle_edit(request, document):
	if request.method == 'POST':
		form = TextForm(request.POST)
		if form.is_valid():
			cleaned_data = form.cleaned_data

			document.title = cleaned_data['title']
			document.text = cleaned_data['text']
			document.author = request.user

			# save the document and also save the user and the comment the user added
			with transaction.atomic(), reversion.create_revision():
				document.save()
				reversion.set_user(request.user)
				reversion.set_comment(cleaned_data['comment'])

			# delete Autosave
			try:
				autosave = TemporaryDocumentText.objects.get(document=document)
				autosave.delete()
			except TemporaryDocumentText.DoesNotExist:
				pass

			return True, form
	else:

		# load Autosave
		try:
			autosave = TemporaryDocumentText.objects.get(document=document)
			text = autosave.text
			autosaved = True
		except TemporaryDocumentText.DoesNotExist:
			text = document.text
			autosaved = False

		if 'restore' not in request.GET:
			text = document.text
		else:
			autosaved = False

		form_data = {
			'title': document.title,
			'text': text,
		}
		form = TextForm(form_data)
		form.autosave = autosaved
		if autosaved:
			form.autosave_date = autosave.created

	return False, form


def handle_autosave(request, document):
	if request.method == 'POST':
		form = TextForm(request.POST)
		form.is_valid()
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


def handle_attachment(request, document):
	if request.method == "POST":
		form = AttachmentForm(request.POST, request.FILES)
		if form.is_valid():
			instance = form.save(commit=False)
			if instance.displayname == '':
				instance.displayname = instance.file.name
			if not re.search(r'\.\w+$', instance.displayname):
				file_type = re.search(r'\.(\w+)$', instance.file.name).group(1)
				instance.displayname = "{}.{}".format(instance.displayname, file_type)
			instance.document = document
			instance.save()
			return True, form
	else:
		form = AttachmentForm()
	return False, form
