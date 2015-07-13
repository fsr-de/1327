import json
import re

from django.db import transaction
from django.conf import settings
from django.utils import timezone
import reversion

from _1327.documents.models import Document, TemporaryDocumentText
from _1327.documents.forms import DocumentForm, AttachmentForm

def get_new_autosaved_pages_for_user(user):
	autosaved_pages = []
	all_temp_documents = TemporaryDocumentText.objects.all()
	for temp_document in all_temp_documents:
		document = temp_document.document
		if len(reversion.get_for_object(document)) == 0 and document.author == user:
			autosaved_pages.append(document)
	return autosaved_pages

def delete_old_empty_pages():
	all_documents = Document.objects.filter(created__lte = timezone.now() - settings.DELETE_EMPTY_PAGE_AFTER)
	for document in all_documents:
		if len(reversion.get_for_object(document)) == 0 and \
			not TemporaryDocumentText.objects.filter(document=document).exists():
				document.delete()

def handle_edit(request, document):
	if request.method == 'POST':
		form = document.Form(request.POST, instance=document)
		if form.is_valid():
			cleaned_data = form.cleaned_data

			document.url_title = cleaned_data['url_title']
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
		autosave = None
		try:
			autosave = TemporaryDocumentText.objects.get(document=document)
			autosaved = True
		except TemporaryDocumentText.DoesNotExist:
			autosaved = False

		if 'restore' in request.GET:
			autosaved = False

		if 'restore' in request.GET and autosave is not None:
			form_data = {
				'text': autosave.text,
				'url_title': document.url_title,
			}
			form = DocumentForm(initial=form_data, instance=document)
		else:
			form = DocumentForm(instance=document)
		form.autosave = autosaved
		if autosaved:
			form.autosave_date = autosave.created

	return False, form


def handle_autosave(request, document):
	if request.method == 'POST':
		form = DocumentForm(request.POST)
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
