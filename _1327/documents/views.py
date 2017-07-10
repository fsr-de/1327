import json
import os

from channels import Group as WebsocketGroup

from django.contrib import messages
from django.contrib.admin.utils import NestedObjects
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.db import DEFAULT_DB_ALIAS, models, transaction
from django.forms import formset_factory
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, Http404, render
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from guardian.shortcuts import get_objects_for_user
from guardian.utils import get_anonymous_user

from reversion import revisions
from reversion.models import Version
from sendfile import sendfile

from _1327 import settings
from _1327.documents.consumers import get_group_name
from _1327.documents.forms import get_permission_form
from _1327.documents.models import Attachment, Document
from _1327.documents.utils import delete_cascade_to_json, delete_old_empty_pages, get_model_function, get_new_autosaved_pages_for_user, \
	handle_attachment, handle_autosave, handle_edit, prepare_versions
from _1327.information_pages.models import InformationDocument
from _1327.information_pages.forms import InformationDocumentForm  # noqa
from _1327.main.utils import convert_markdown, document_permission_overview
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
	document = get_object_or_404(Document, url_title=title)
	content_type = ContentType.objects.get_for_model(document)
	if document.has_perms():
		check_permissions(document, request.user, [document.edit_permission_name])
	elif new_autosaved_pages is None and initial is None:
		# page is not new and has no permissions set, it is likely that somebody tries to view an autosaved page
		# users are only allowed to view autosaved pages if they have the "add" permission for documents
		check_permissions(document, request.user, [document.add_permission_name])

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
		return HttpResponseRedirect(reverse(document.get_view_url_name(), args=[document.url_title]))
	else:
		return render(request, template_name, {
			'document': document,
			'form': form,
			'attachment_form': attachment_form,
			'active_page': 'edit',
			'creation': document.is_in_creation,
			'new_autosaved_pages': new_autosaved_pages,
			'permission_overview': document_permission_overview(request.user, document),
			'supported_image_types': settings.SUPPORTED_IMAGE_TYPES,
			'formset': formset,
		})


def autosave(request, title):
	if request.user.is_anonymous or request.user == get_anonymous_user():
		raise PermissionDenied()

	document = None
	try:
		document = get_object_or_404(Document, url_title=title)
		if document.has_perms():
			check_permissions(document, request.user, [document.edit_permission_name])
	except Document.DoesNotExist:
		pass

	handle_autosave(request, document)

	data = {
		'preview_url': request.build_absolute_uri(
			reverse('documents:preview') + '?hash_value=' + document.hash_value
		)
	}

	return HttpResponse(json.dumps(data))


def versions(request, title):
	document = get_object_or_404(Document, url_title=title)
	check_permissions(document, request.user, [document.edit_permission_name])
	document_versions = prepare_versions(document)

	if not document.can_be_reverted:
		messages.warning(request, _('This Document can not be reverted!'))

	return render(request, 'documents_versions.html', {
		'active_page': 'versions',
		'versions': document_versions,
		'document': document,
		'permission_overview': document_permission_overview(request.user, document),
		'can_be_reverted': document.can_be_reverted,
	})


def view(request, title):
	document = get_object_or_404(Document, url_title=title)
	content_type = ContentType.objects.get_for_model(document)
	check_permissions(document, request.user, [document.view_permission_name])

	try:
		function = get_model_function(content_type, 'view')
		return function(request, title)
	except (ImportError, AttributeError):
		pass

	text, toc = convert_markdown(document.text)

	return render(request, 'documents_base.html', {
		'document': document,
		'text': text,
		'toc': toc,
		'attachments': document.attachments.filter(no_direct_download=False).order_by('index'),
		'active_page': 'view',
		'view_page': True,
		'permission_overview': document_permission_overview(request.user, document),
	})


def permissions(request, title):
	document = get_object_or_404(Document, url_title=title)
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
			return HttpResponseRedirect(reverse(document.get_permissions_url_name(), args=[document.url_title]))
		if request.user.has_perm(document.view_permission_name, document):
			return HttpResponseRedirect(reverse(document.get_view_url_name(), args=[document.url_title]))
		return HttpResponseRedirect(reverse('index'))

	return render(request, 'documents_permissions.html', {
		'document': document,
		'formset_header': PermissionForm.header(content_type),
		'formset': formset,
		'active_page': 'permissions',
		'permission_overview': document_permission_overview(request.user, document),
	})


def publish(request, title, state_id):
	document = get_object_or_404(Document, url_title=title)
	check_permissions(document, request.user, [document.edit_permission_name])
	if not document.show_publish_button():
		raise PermissionDenied()

	document.publish(state_id)
	messages.success(request, _("Minutes document has been published."))

	return HttpResponseRedirect(reverse(document.get_view_url_name(), args=[document.url_title]))


def attachments(request, title):
	document = get_object_or_404(Document, url_title=title)
	check_permissions(document, request.user, [document.edit_permission_name])

	success, form, __ = handle_attachment(request, document)
	if success:
		messages.success(request, _("File has been uploaded successfully!"))
		return HttpResponseRedirect(reverse(document.get_attachments_url_name(), args=[document.url_title]))
	else:
		return render(request, "documents_attachments.html", {
			'document': document,
			'edit_url': reverse(document.get_attachments_url_name(), args=[document.url_title]),
			'form': form,
			'attachments': document.attachments.all().order_by('index'),
			'active_page': 'attachments',
			'permission_overview': document_permission_overview(request.user, document),
		})


def render_text(request, title):
	if request.method != 'POST':
		raise SuspiciousOperation

	document = get_object_or_404(Document, url_title=title)
	if document.has_perms():
		check_permissions(document, request.user, [document.view_permission_name, document.edit_permission_name])

	text, __ = convert_markdown(request.POST['text'])

	WebsocketGroup(get_group_name(document.hash_value)).send({
		'text': text
	})

	return HttpResponse(text, content_type='text/plain')


def search(request):
	if not request.GET:
		raise Http404

	id_only = request.GET.get('id_only', False)

	minutes = get_objects_for_user(request.user, MinutesDocument.VIEW_PERMISSION_NAME, klass=MinutesDocument.objects.filter(title__icontains=request.GET['q']))
	information_documents = get_objects_for_user(request.user, InformationDocument.VIEW_PERMISSION_NAME, klass=InformationDocument.objects.filter(title__icontains=request.GET['q']))
	polls = get_objects_for_user(request.user, Poll.VIEW_PERMISSION_NAME, klass=Poll.objects.filter(title__icontains=request.GET['q']))

	return render(request, "ajax_search_api.json", {
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
	document = get_object_or_404(Document, url_title=document_url_title)
	check_permissions(document, request.user, [document.edit_permission_name])
	versions = Version.objects.get_for_object(document)

	if not document.can_be_reverted:
		raise SuspiciousOperation('This Document can not be reverted!')

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
	document_class = ContentType.objects.get_for_id(fields.pop('polymorphic_ctype_id')).model_class()

	# Remove all references to parent objects, rename ForeignKeyFields, extract ManyToManyFields.
	new_fields = fields.copy()
	many_to_many_fields = {}
	for key in fields.keys():
		if "_ptr" in key:
			del new_fields[key]
			continue

		try:
			field = getattr(document_class, key).field
		except AttributeError:
			continue

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

	return HttpResponse(reverse('versions', args=[reverted_document.url_title]))


def create_attachment(request):
	if not request.is_ajax() or not request.method == "POST":
		raise Http404()

	document = get_object_or_404(Document, id=request.POST['document'])
	if not document.can_be_changed_by(request.user):
		raise PermissionDenied

	success, __, attachment = handle_attachment(request, document)
	if success:
		return HttpResponse(attachment.hash_value)
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

	attachment = get_object_or_404(Attachment, hash_value=request.GET['hash_value'])
	# check whether user is allowed to see that document and thus download the attachment
	document = attachment.document
	if not request.user.has_perm(document.view_permission_name, document):
		raise PermissionDenied

	filename = os.path.join(settings.MEDIA_ROOT, attachment.file.name)
	extension = os.path.splitext(filename)[1]
	is_attachment = not request.GET.get('embed', None)

	attachment_filename = attachment.displayname
	if not attachment_filename.endswith(extension):
		attachment_filename += extension

	return sendfile(request, filename, attachment=is_attachment, attachment_filename=attachment_filename)


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

	document = get_object_or_404(Document, pk=document_id)
	if not document.can_be_changed_by(request.user):
		raise PermissionDenied

	attachments = document.attachments.all()
	data = {}
	for attachment in attachments:
		file_type = attachment.displayname.lower().split('.')[-1]
		if file_type not in settings.SUPPORTED_IMAGE_TYPES:
			continue
		data[attachment.hash_value] = attachment.displayname

	return HttpResponse(json.dumps(data))


def change_attachment(request):
	if not request.POST or not request.is_ajax():
		raise Http404

	attachment_id = request.POST.get('id', None)
	if attachment_id is None:
		raise SuspiciousOperation

	attachment = Attachment.objects.get(id=attachment_id)
	if not attachment.document.can_be_changed_by(request.user):
		raise PermissionDenied

	no_direct_download_value = request.POST.get('no_direct_download', None)
	attachment.no_direct_download = json.loads(no_direct_download_value) if no_direct_download_value is not None else attachment.no_direct_download
	attachment.displayname = request.POST.get('displayname', attachment.displayname)
	attachment.save()
	return HttpResponse()


def delete_document(request, title):
	document = get_object_or_404(Document, url_title=title)
	check_permissions(document, request.user, [document.edit_permission_name])
	document.delete()

	messages.success(request, _("Successfully deleted document: {}".format(document.title)))
	return HttpResponse()


def get_delete_cascade(request, title):
	document = get_object_or_404(Document, url_title=title)
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


def preview(request):
	if not request.GET or request.method != 'GET':
		raise Http404

	hash_value = request.GET['hash_value']
	document = get_object_or_404(Document, hash_value=hash_value)

	text, __ = convert_markdown(document.text)

	return render(
		request,
		'documents_preview.html',
		{
			'title': document.title,
			'text': text,
			'preview_url': settings.PREVIEW_URL,
			'hash_value': hash_value,
		}
	)
