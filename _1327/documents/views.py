import json
import os

from django.contrib import messages
from django.contrib.admin.utils import NestedObjects
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.core.urlresolvers import reverse
from django.db import DEFAULT_DB_ALIAS, models, transaction
from django.forms import formset_factory
from django.http import HttpResponse, HttpResponseRedirect

from django.shortcuts import get_object_or_404, Http404, render
from django.utils.translation import ugettext_lazy as _
from guardian.shortcuts import get_objects_for_user

import markdown
from markdown.extensions.toc import TocExtension
from reversion import revisions
from sendfile import sendfile

from _1327 import settings
from _1327.documents.forms import get_permission_form
from _1327.documents.markdown_internal_link_extension import InternalLinksMarkdownExtension
from _1327.documents.models import Attachment, Document
from _1327.documents.utils import delete_cascade_to_json, delete_old_empty_pages, get_model_function, get_new_autosaved_pages_for_user, \
	handle_attachment, handle_autosave, handle_edit, permission_warning, prepare_versions
from _1327.information_pages.models import InformationDocument
from _1327.information_pages.forms import InformationDocumentForm  # noqa
from _1327.main.utils import abbreviation_explanation_markdown
from _1327.minutes.models import MinutesDocument
from _1327.minutes.forms import MinutesDocumentForm  # noqa
from _1327.polls.models import Poll
from _1327.polls.forms import PollForm  # noqa
from _1327.user_management.shortcuts import check_permissions


def create(request, document_type):
	content_type = ContentType.objects.get(model=document_type)
	if request.user.has_perm("{app}.add_{model}".format(app=content_type.app_label, model=content_type.model)):
		model_class = content_type.model_class()
		delete_old_empty_pages()
		title = model_class.generate_new_title()
		url_title = model_class.generate_default_slug(title)
		kwargs = {
			'url_title': url_title,
			'title': title,
		}
		if hasattr(model_class, 'author'):
			kwargs['author'] = request.user
		if hasattr(model_class, 'moderator'):
			kwargs['moderator'] = request.user
		model_class.objects.get_or_create(**kwargs)
		new_autosaved_pages = get_new_autosaved_pages_for_user(request.user, content_type)
		initial = {
			'comment': _("Created document"),
		}
		return edit(request, url_title, new_autosaved_pages, initial)
	else:
		raise PermissionDenied


def edit(request, title, new_autosaved_pages=None, initial=None):
	document = Document.objects.get(url_title=title)
	content_type = ContentType.objects.get_for_model(document)
	if document.has_perms():
		check_permissions(document, request.user, [document.edit_permission_name])

	# if the edit form has a formset we will initialize it here
	formset_factory = document.Form.get_formset_factory()
	formset = formset_factory(request.POST or None, instance=document) if formset_factory is not None else None

	if formset is not None:
		template_name = "{app}_edit.html".format(app=content_type.app_label)
	else:
		template_name = "documents_edit.html"

	success, form = handle_edit(request, document, formset, initial)
	__, attachment_form, __ = handle_attachment(request, document)

	if success:
		messages.success(request, _("Successfully saved changes"))
		return HttpResponseRedirect(reverse('documents:view', args=[document.url_title]))
	else:
		return render(request, template_name, {
			'document': document,
			'form': form,
			'attachment_form': attachment_form,
			'active_page': 'edit',
			'creation': (len(revisions.get_for_object(document)) == 0),
			'new_autosaved_pages': new_autosaved_pages,
			'permission_warning': permission_warning(request.user, content_type, document),
			'supported_image_types': settings.SUPPORTED_IMAGE_TYPES,
			'formset': formset,
		})


def autosave(request, title):
	document = None
	try:
		document = Document.objects.get(url_title=title)
		if document.has_perms():
			check_permissions(document, request.user, [document.edit_permission_name])
	except Document.DoesNotExist:
		pass

	handle_autosave(request, document)
	return HttpResponse()


def versions(request, title):
	document = Document.objects.get(url_title=title)
	content_type = ContentType.objects.get_for_model(document)
	check_permissions(document, request.user, [document.edit_permission_name])
	document_versions = prepare_versions(document)

	return render(request, 'documents_versions.html', {
		'active_page': 'versions',
		'versions': document_versions,
		'document': document,
		'permission_warning': permission_warning(request.user, content_type, document),
	})


def view(request, title):
	document = Document.objects.get(url_title=title)
	content_type = ContentType.objects.get_for_model(document)
	check_permissions(document, request.user, [document.view_permission_name])

	try:
		function = get_model_function(content_type, 'view')
		return function(request, title)
	except (ImportError, AttributeError):
		pass

	md = markdown.Markdown(safe_mode='escape', extensions=[TocExtension(baselevel=2), InternalLinksMarkdownExtension(), 'markdown.extensions.abbr'])
	text = md.convert(document.text + abbreviation_explanation_markdown())

	return render(request, 'documents_base.html', {
		'document': document,
		'text': text,
		'toc': md.toc,
		'attachments': document.attachments.filter(no_direct_download=False).order_by('index'),
		'active_page': 'view',
		'permission_warning': permission_warning(request.user, content_type, document),
	})


def permissions(request, title):
	document = Document.objects.get(url_title=title)
	content_type = ContentType.objects.get_for_model(document)
	check_permissions(document, request.user, [document.edit_permission_name])
	if not document.show_permissions_editor():
		raise PermissionDenied()
	PermissionForm = get_permission_form(document)
	PermissionFormset = formset_factory(get_permission_form(document), extra=0)

	initial_data = PermissionForm.prepare_initial_data(Group.objects.all(), content_type, document)
	formset = PermissionFormset(request.POST or None, initial=initial_data)
	if request.POST and formset.is_valid():
		for form in formset:
			form.save(document)
		messages.success(request, _("Permissions have been changed successfully."))

		if request.user.has_perm(document.edit_permission_name, document):
			return HttpResponseRedirect(reverse('documents:permissions', args=[document.url_title]))
		if request.user.has_perm(document.view_permission_name, document):
			return HttpResponseRedirect(reverse('documents:view', args=[document.url_title]))
		return HttpResponseRedirect(reverse('index'))

	return render(request, 'documents_permissions.html', {
		'document': document,
		'formset_header': PermissionForm.header(content_type),
		'formset': formset,
		'active_page': 'permissions',
		'permission_warning': permission_warning(request.user, content_type, document),
	})


def publish(request, title):
	document = Document.objects.get(url_title=title)
	check_permissions(document, request.user, [document.edit_permission_name])
	if not document.show_publish_button():
		raise PermissionDenied()

	document.publish()
	messages.success(request, _("Minutes document has been published."))

	return HttpResponseRedirect(reverse("documents:view", args=[document.url_title]))


def attachments(request, title):
	document = Document.objects.get(url_title=title)
	content_type = ContentType.objects.get_for_model(document)
	check_permissions(document, request.user, [document.edit_permission_name])

	success, form, __ = handle_attachment(request, document)
	if success:
		messages.success(request, _("File has been uploaded successfully!"))
		return HttpResponseRedirect(reverse("documents:attachments", args=[document.url_title]))
	else:
		return render(request, "documents_attachments.html", {
			'document': document,
			'edit_url': reverse('documents:attachments', args=[document.url_title]),
			'form': form,
			'attachments': document.attachments.all().order_by('index'),
			'active_page': 'attachments',
			'permission_warning': permission_warning(request.user, content_type, document),
		})


def render_text(request, title):
	if request.method != 'POST':
		raise SuspiciousOperation

	document = Document.objects.get(url_title=title)
	if document.has_perms():
		check_permissions(document, request.user, [document.view_permission_name, document.edit_permission_name])

	text = request.POST['text']
	md = markdown.Markdown(safe_mode='escape', extensions=[TocExtension(baselevel=2), InternalLinksMarkdownExtension(), 'markdown.extensions.abbr'])
	text = md.convert(text + abbreviation_explanation_markdown())
	return HttpResponse(text, content_type='text/plain')


def search(request):
	if not request.GET:
		raise Http404

	id_only = request.GET.get('id_only', False)

	minutes = get_objects_for_user(request.user, MinutesDocument.VIEW_PERMISSION_NAME, klass=MinutesDocument.objects.filter(title__icontains=request.GET['q']))
	information_documents = get_objects_for_user(request.user, InformationDocument.VIEW_PERMISSION_NAME, klass=InformationDocument.objects.filter(title__icontains=request.GET['q']))
	polls = get_objects_for_user(request.user, Poll.VIEW_PERMISSION_NAME, klass=Poll.objects.filter(title__icontains=request.GET['q']))

	return render(request, "search_api.json", {
		'minutes': minutes,
		'information_documents': information_documents,
		'polls': polls,
		'id_only': id_only,
	})


def revert(request):
	if not request.is_ajax() or not request.POST:
		raise Http404

	version_id = request.POST['id']
	document_url_title = request.POST['url_title']
	document = Document.objects.get(url_title=document_url_title)
	check_permissions(document, request.user, [document.edit_permission_name])
	versions = revisions.get_for_object(document)

	# find the we want to revert to
	revert_version = None
	for version in versions:
		if version.pk == int(version_id):
			revert_version = version
			break

	if revert_version is None:
		# user supplied version_id that does not exist
		raise SuspiciousOperation('Could not find document')

	revert_version.revision.revert(delete=False)
	fields = revert_version.field_dict
	document_class = ContentType.objects.get_for_id(fields.pop('polymorphic_ctype')).model_class()

	# Remove all references to parent objects, rename ForeignKeyFields, extract ManyToManyFields.
	new_fields = fields.copy()
	many_to_many_fields = {}
	for key in fields.keys():
		if "_ptr" in key:
			del new_fields[key]
			continue
		if hasattr(document_class, key):
			field = getattr(document_class, key).field
			if isinstance(field, models.ManyToManyField):
				many_to_many_fields[key] = fields[key]
			else:
				new_fields[field.attname] = fields[key]
			del new_fields[key]

	reverted_document = document_class(**new_fields)
	with transaction.atomic(), revisions.create_revision():
		reverted_document.save()
		# Restore ManyToManyFields
		for key in many_to_many_fields.keys():
			getattr(reverted_document, key).clear()
			getattr(reverted_document, key).add(*many_to_many_fields[key])
		revisions.set_user(request.user)
		revisions.set_comment(
			_('reverted to revision \"{revision_comment}\"'.format(revision_comment=revert_version.revision.comment)))

	return HttpResponse()


def create_attachment(request):
	if not request.is_ajax() or not request.method == "POST":
		raise Http404()

	document = Document.objects.get(id=request.POST['document'])
	if not document.can_be_changed_by(request.user):
		raise PermissionDenied

	success, __, attachment = handle_attachment(request, document)
	if success:
		return HttpResponse(attachment.id)
	else:
		raise SuspiciousOperation


def delete_attachment(request):
	if request.is_ajax() and request.method == "POST":
		attachment = Attachment.objects.get(id=request.POST['id'])
		# check whether user has permission to change the document the attachment belongs to
		document = attachment.document
		if not document.can_be_changed_by(request.user):
			raise PermissionDenied

		attachment.file.delete()
		attachment.delete()
		messages.success(request, _("Successfully deleted Attachment!"))
		return HttpResponse()
	raise Http404()


def download_attachment(request):
	if not request.method == "GET":
		raise SuspiciousOperation

	attachment = get_object_or_404(Attachment, pk=request.GET['attachment_id'])
	# check whether user is allowed to see that document and thus download the attachment
	document = attachment.document
	if not request.user.has_perm(document.VIEW_PERMISSION_NAME, document):
		raise PermissionDenied

	filename = os.path.join(settings.MEDIA_ROOT, attachment.file.name)
	is_attachment = not request.GET.get('embed', None)

	return sendfile(request, filename, attachment=is_attachment, attachment_filename=attachment.displayname)


def update_attachment_order(request):
	data = request.POST
	if data is None or not request.is_ajax():
		raise Http404

	for pk, index in data._iteritems():
		attachment = get_object_or_404(Attachment, pk=pk)
		# check that user is allowed to make changes to attachment
		document = attachment.document
		if not document.can_be_changed_by(request.user):
			raise PermissionDenied

		attachment.index = index
		attachment.save()
	return HttpResponse()


def get_attachments(request, document_id):
	if not request.is_ajax():
		raise Http404

	document = Document.objects.get(pk=document_id)
	if not document.can_be_changed_by(request.user):
		raise PermissionDenied

	attachments = document.attachments.all()
	data = {}
	for attachment in attachments:
		file_type = attachment.displayname.lower().split('.')[-1]
		if file_type not in settings.SUPPORTED_IMAGE_TYPES:
			continue
		data[attachment.id] = attachment.displayname

	return HttpResponse(json.dumps(data))


def change_attachment_no_direct_download(request):
	if not request.POST or not request.is_ajax():
		raise Http404

	attachment_id = request.POST['id']
	no_direct_download = json.loads(request.POST['no_direct_download'])

	attachment = Attachment.objects.get(pk=attachment_id)
	if not attachment.document.can_be_changed_by(request.user):
		raise PermissionDenied

	attachment.no_direct_download = no_direct_download
	attachment.save()
	return HttpResponse()


def delete_document(request, title):
	document = Document.objects.get(url_title=title)
	check_permissions(document, request.user, [document.edit_permission_name])
	document.delete()

	messages.success(request, _("Successfully deleted document: {}".format(document.title)))
	return HttpResponse()


def get_delete_cascade(request, title):
	document = Document.objects.get(url_title=title)
	check_permissions(document, request.user, [document.edit_permission_name])

	collector = NestedObjects(using=DEFAULT_DB_ALIAS)
	collector.collect([document])
	delete_cascade = collector.nested()

	# remove all subclasses of current document from the list because that does not add much helpful information
	simplified_delete_cascade = []
	for cascade_item in delete_cascade:
		if issubclass(type(document), type(cascade_item)) and not type(document) == type(cascade_item):
			continue
		simplified_delete_cascade.append(cascade_item)

	return HttpResponse(json.dumps(delete_cascade_to_json(simplified_delete_cascade)))
