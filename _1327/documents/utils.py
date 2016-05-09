import json
import re

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.utils import timezone
from guardian.utils import get_anonymous_user
from reversion import revisions

from _1327.documents.forms import AttachmentForm, DocumentForm
from _1327.documents.models import Document, TemporaryDocumentText
from _1327.minutes.models import MinutesDocument


def get_new_autosaved_pages_for_user(user):
	autosaved_pages = []
	all_temp_documents = TemporaryDocumentText.objects.all()
	for temp_document in all_temp_documents:
		document = temp_document.document
		if len(revisions.get_for_object(document)) == 0 and temp_document.author == user:
			autosaved_pages.append(document)
	return autosaved_pages


def delete_old_empty_pages():
	all_documents = Document.objects.filter(created__lte=timezone.now() - settings.DELETE_EMPTY_PAGE_AFTER)
	for document in all_documents:
		if len(revisions.get_for_object(document)) == 0 and \
			not TemporaryDocumentText.objects.filter(document=document).exists():
				document.delete()


def handle_edit(request, document, formset=None):
	if request.method == 'POST':
		form = document.Form(request.POST, instance=document, user=request.user)
		if form.is_valid() and (formset is None or formset.is_valid()):
			cleaned_data = form.cleaned_data

			document.url_title = cleaned_data['url_title']

			# save the document and also save the user and the comment the user added
			with transaction.atomic(), revisions.create_revision():
				content_type = ContentType.objects.get_for_model(document)
				if content_type == ContentType.objects.get_for_model(MinutesDocument):
					document.participants.clear()
					for participant in cleaned_data['participants']:
						document.participants.add(participant)
					document.labels.clear()
					for label in cleaned_data['labels']:
						document.labels.add(label)
					document.groups.clear()
					for group in cleaned_data['groups']:
						document.groups.add(group)
				document.save()
				if formset:
					guests = formset.save(commit=False)
					for guest in formset.deleted_objects:
						guest.delete()
					for guest in guests:
						guest.minute = document
						guest.save()
				revisions.set_user(request.user)
				revisions.set_comment(cleaned_data['comment'])

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
			form = document.Form(initial=form_data, instance=document, user=request.user)
		else:
			form = document.Form(instance=document, user=request.user)
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
			if not re.search(r'\.\w+$', instance.displayname):
				file_type = re.search(r'\.(\w+)$', instance.file.name).group(1)
				instance.displayname = "{}.{}".format(instance.displayname, file_type)
			instance.document = document
			instance.index = document.attachments.count() + 1
			instance.save()
			return True, form, instance
	else:
		form = AttachmentForm()
	return False, form, None


def permission_warning(user, content_type, document):
	anonymous_rights = get_anonymous_user().has_perm(content_type.model_class().VIEW_PERMISSION_NAME, document)
	edit_rights = user.has_perm("change_informationdocument", document)
	return edit_rights and not anonymous_rights
