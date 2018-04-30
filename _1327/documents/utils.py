from functools import lru_cache
import json
import re


from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import SuspiciousOperation
from django.db import transaction
from django.shortcuts import Http404
from django.utils import timezone
from guardian.core import ObjectPermissionChecker
from reversion import revisions
from reversion.models import Version

from _1327.documents.forms import AttachmentForm
from _1327.documents.models import Document, TemporaryDocumentText


def get_new_autosaved_pages_for_user(user, content_type):
	autosaved_pages = []
	all_temp_documents = TemporaryDocumentText.objects.filter(author=user)
	for temp_document in all_temp_documents:
		document = temp_document.document
		# if contenttype of autosave does not match contenttype of current document we will not show this autosave
		if ContentType.objects.get_for_model(document) != content_type:
			continue
		if len(Version.objects.get_for_object(document)) == 0:
			autosaved_pages.append(temp_document)
	return autosaved_pages


def delete_old_empty_pages():
	all_documents = Document.objects.filter(created__lte=timezone.now() - settings.DELETE_EMPTY_PAGE_AFTER)
	for document in all_documents:
		if len(Version.objects.get_for_object(document)) == 0 and \
			not TemporaryDocumentText.objects.filter(document=document).exists():
				document.delete()


def handle_edit(request, document, formset=None, initial=None, creation_group=None):
	if request.method == 'POST':
		creation = document.is_in_creation
		form = document.Form(request.POST, instance=document, initial=initial, user=request.user, creation=creation, creation_group=creation_group)
		if form.is_valid() and (formset is None or formset.is_valid()):
			cleaned_data = form.cleaned_data

			document.url_title = cleaned_data['url_title']

			# remove trailing slash if user tries to set custom url with trailing slash
			if document.url_title.endswith('/'):
				document.url_title = document.url_title[:-1]

			# save the document and also save the user and the comment the user added
			with transaction.atomic():
				# handle_edit has to happen outside of create_revision, because otherwise versions will not be
				# created correctly, if the model, that is getting saved, contains many-to-many relationships
				document.handle_edit(cleaned_data)

				# make sure to remove temp prefix of url_title
				if document.url_title.startswith('temp_'):
					temp_prefix_len = re.search(r'temp_\d+_', document.url_title).end()
					document.url_title = document.url_title[temp_prefix_len:]
				# check that there is no document that already has that url
				if Document.objects.filter(url_title=document.url_title).exclude(id=document.id).exists():
					document.url_title = document.generate_default_slug(document.url_title)

				with revisions.create_revision():
					document.save()
					document.save_formset(formset)
					revisions.set_user(request.user)
					revisions.set_comment(cleaned_data['comment'])

			if not document.has_perms() or creation:
				document.set_all_permissions(cleaned_data['group'])

			# delete Autosave
			try:
				autosaves = TemporaryDocumentText.objects.filter(document=document)
				for autosave in autosaves:
					autosave.delete()
			except TemporaryDocumentText.DoesNotExist:
				pass

			return True, form
	else:
		# load Autosave
		autosaves = TemporaryDocumentText.objects.filter(document=document, author=request.user)
		autosaved = autosaves.count() > 0

		if 'restore' in request.GET and autosaved:
			autosave_to_restore = None
			for autosave in autosaves:
				if int(request.GET['restore']) == autosave.id:
					autosave_to_restore = autosave

			if autosave_to_restore is None:
				raise SuspiciousOperation

			form_data = {
				'text': autosave_to_restore.text,
				'url_title': document.url_title,
			}
			if initial is None:
				initial = {}
			initial.update(form_data)
			autosaved = False

		form = document.Form(initial=initial, instance=document, user=request.user, creation=document.is_in_creation, creation_group=creation_group)

		form.autosaved = autosaved
		if autosaved:
			form.autosaves = autosaves

	return False, form


def handle_autosave(request, document):
	if request.method == 'POST':
		form = document.Form(request.POST, user=request.user, creation=document.is_in_creation, instance=document)
		form.is_valid()
		text_strip = request.POST['text'].strip()
		if text_strip != '':
			cleaned_data = form.cleaned_data

			if document is None:
				temporary_document_text = TemporaryDocumentText.objects.create(author=request.user)
			else:
				temporary_document_text, __ = TemporaryDocumentText.objects.get_or_create(document=document, author=request.user)

			temporary_document_text.text = cleaned_data['text']
			temporary_document_text.save()


def prepare_versions(document):
	versions = Version.objects.get_for_object(document).reverse()

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


def get_permitted_documents(documents, request, groupid):
	groupid = int(groupid)
	try:
		group = Group.objects.get(id=groupid)
	except ObjectDoesNotExist:
		raise Http404

	own_group = request.user.is_superuser or group in request.user.groups.all()

	# Prefetch group permissions
	group_checker = ObjectPermissionChecker(group)
	group_checker.prefetch_perms(documents)

	# Prefetch user permissions
	user_checker = ObjectPermissionChecker(request.user)
	user_checker.prefetch_perms(documents)

	# Prefetch ip group permissions
	ip_range_group_name = request.user._ip_range_group_name if hasattr(request.user, '_ip_range_group_name') else None
	if ip_range_group_name:
		ip_range_group = Group.objects.get(name=ip_range_group_name)
		ip_range_group_checker = ObjectPermissionChecker(ip_range_group)

	permitted_documents = []
	for d in documents:
		# we show all documents for which the requested group has edit permissions
		# e.g. if you request FSR documents, all documents for which the FSR group has edit rights will be shown
		if not group_checker.has_perm(d.edit_permission_name, d):
			continue
		# we only show documents for which the user has view permissions
		if not user_checker.has_perm(Document.get_view_permission(), d) and (not ip_range_group_name or not ip_range_group_checker.has_perm(Document.get_view_permission(), d)):
			continue
		permitted_documents.append(d)

	return permitted_documents, own_group
