from functools import lru_cache

import json

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.utils import timezone
from reversion import revisions

from _1327.documents.forms import AttachmentForm, DocumentForm
from _1327.documents.models import Document, TemporaryDocumentText


def get_new_autosaved_pages_for_user(user, content_type):
	autosaved_pages = []
	all_temp_documents = TemporaryDocumentText.objects.filter(author=user)
	for temp_document in all_temp_documents:
		document = temp_document.document
		# if contenttype of autosave does not match contenttype of current document we will not show this autosave
		if ContentType.objects.get_for_model(document) != content_type:
			continue
		if len(revisions.get_for_object(document)) == 0:
			autosaved_pages.append(document)
	return autosaved_pages


def delete_old_empty_pages():
	all_documents = Document.objects.filter(created__lte=timezone.now() - settings.DELETE_EMPTY_PAGE_AFTER)
	for document in all_documents:
		if len(revisions.get_for_object(document)) == 0 and \
			not TemporaryDocumentText.objects.filter(document=document).exists():
				document.delete()


def handle_edit(request, document, formset=None, initial=None):
	if request.method == 'POST':
		creation = document.is_in_creation
		form = document.Form(request.POST, instance=document, initial=initial, user=request.user, creation=creation)
		if form.is_valid() and (formset is None or formset.is_valid()):
			cleaned_data = form.cleaned_data

			document.url_title = cleaned_data['url_title']

			# remove trailing slash if user tries to set custom url with trailing slash
			if document.url_title.endswith('/'):
				document.url_title = document.url_title[:-1]

			# save the document and also save the user and the comment the user added
			with transaction.atomic(), revisions.create_revision():
				document.handle_edit(cleaned_data)
				document.save()
				document.save_formset(formset)
				revisions.set_user(request.user)
				revisions.set_comment(cleaned_data['comment'])

			if not document.has_perms() or creation:
				document.set_all_permissions(cleaned_data['group'])

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
			if initial is None:
				initial = {}
			initial.update(form_data)

		form = document.Form(initial=initial, instance=document, user=request.user, creation=document.is_in_creation)

		form.autosave = autosaved
		if autosaved:
			form.autosave_date = autosave.created

	return False, form


def handle_autosave(request, document):
	if request.method == 'POST':
		form = DocumentForm(request.POST, user=request.user, creation=document.is_in_creation)
		form.is_valid()
		text_strip = request.POST['text'].strip()
		if text_strip != '':
			cleaned_data = form.cleaned_data

			if document is None:
				temporary_document_text = TemporaryDocumentText(author=request.user)
			elif document.text != cleaned_data['text']:
				temporary_document_text, __ = TemporaryDocumentText.objects.get_or_create(document=document, author=request.user)
				temporary_document_text.document = document
			else:
				return

			temporary_document_text.text = cleaned_data['text']
			temporary_document_text.save()


def prepare_versions(document):
	versions = revisions.get_for_object(document).reverse()

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
			instance.document = document
			instance.index = document.attachments.count() + 1
			instance.save()
			return True, form, instance
	else:
		form = AttachmentForm()
	return False, form, None


@lru_cache(maxsize=32)
def get_model_function(content_type, function_name):
	module = __import__('_1327.{content_type}.views'.format(content_type=content_type.app_label), fromlist=[function_name])
	return getattr(module, function_name)


def delete_cascade_to_json(cascade):
	items = []
	for cascade_item in cascade:
		if hasattr(cascade_item, '__iter__'):
			items.append(delete_cascade_to_json(cascade_item))
		else:
			items.append({
				"type": type(cascade_item).__name__,
				"name": str(cascade_item),
			})
	return items
