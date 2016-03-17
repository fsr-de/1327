from datetime import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.forms.formsets import formset_factory
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import render
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from guardian.models import Group
import markdown
from markdown.extensions.toc import TocExtension
from reversion import revisions

from _1327.documents.forms import get_permission_form
from _1327.documents.models import Document
from _1327.documents.utils import (
	delete_old_empty_pages,
	get_new_autosaved_pages_for_user,
	handle_attachment,
	handle_autosave,
	handle_edit,
	permission_warning,
	prepare_versions,
)
from _1327.information_pages.models import InformationDocument
from _1327.user_management.shortcuts import get_object_or_error


def create(request):
	if request.user.has_perm("information_pages.add_informationdocument"):
		delete_old_empty_pages()
		title = _("New Page from {}").format(str(datetime.now()))
		url_title = slugify(title)
		InformationDocument.objects.get_or_create(url_title=url_title, title=title)
		new_autosaved_pages = get_new_autosaved_pages_for_user(request.user)
		return edit(request, url_title, new_autosaved_pages)
	else:
		return HttpResponseForbidden()


def edit(request, title, new_autosaved_pages=None):
	document = get_object_or_error(InformationDocument, request.user, ['information_pages.change_informationdocument'], url_title=title)

	success, form = handle_edit(request, document)
	__, attachment_form, __ = handle_attachment(request, document)

	if success:
		messages.success(request, _("Successfully saved changes"))
		return HttpResponseRedirect(reverse('information_pages:view_information', args=[document.url_title]))
	else:
		return render(request, "information_pages_edit.html", {
			'document': document,
			'form': form,
			'attachment_form': attachment_form,
			'active_page': 'edit',
			'creation': (len(revisions.get_for_object(document)) == 0),
			'new_autosaved_pages': new_autosaved_pages,
			'permission_warning': permission_warning(request.user, document),
			'supported_image_types': settings.SUPPORTED_IMAGE_TYPES,
		})


def autosave(request, title):
	document = None
	try:
		document = get_object_or_error(InformationDocument, request.user, ['information_pages.change_informationdocument'], url_title=title)
	except Document.DoesNotExist:
		pass

	handle_autosave(request, document)
	return HttpResponse()


def versions(request, title):
	# get all versions of the document
	document = get_object_or_error(InformationDocument, request.user, ['information_pages.change_informationdocument'], url_title=title)
	document_versions = prepare_versions(document)

	return render(request, 'information_pages_versions.html', {
		'active_page': 'versions',
		'versions': document_versions,
		'document': document,
		'permission_warning': permission_warning(request.user, document),
	})


def view_information(request, title):
	document = get_object_or_error(InformationDocument, request.user, [InformationDocument.get_view_permission()], url_title=title)

	md = markdown.Markdown(safe_mode='escape', extensions=[TocExtension(baselevel=2)])
	text = md.convert(document.text)

	return render(request, 'information_pages_base.html', {
		'document': document,
		'text': text,
		'toc': md.toc,
		'attachments': document.attachments.filter(no_direct_download=False).order_by('index'),
		'active_page': 'view',
		'permission_warning': permission_warning(request.user, document),
	})


def permissions(request, title):
	document = get_object_or_error(InformationDocument, request.user, ['information_pages.change_informationdocument'], url_title=title)

	content_type = ContentType.objects.get_for_model(InformationDocument)
	PermissionForm = get_permission_form(content_type)
	PermissionFormset = formset_factory(get_permission_form(content_type), extra=0)

	initial_data = PermissionForm.prepare_initial_data(Group.objects.all(), content_type, document)
	formset = PermissionFormset(request.POST or None, initial=initial_data)
	if request.POST and formset.is_valid():
		for form in formset:
			form.save(document)
		messages.success(request, _("Permissions have been changed successfully."))

		return HttpResponseRedirect(reverse('information_pages:permissions', args=[document.url_title]))

	return render(request, 'information_pages_permissions.html', {
		'document': document,
		'formset_header': PermissionForm.header(),
		'formset': formset,
		'active_page': 'permissions',
		'permission_warning': permission_warning(request.user, document),
	})


def attachments(request, title):
	document = get_object_or_error(InformationDocument, request.user, ['information_pages.change_informationdocument'], url_title=title)

	success, form, __ = handle_attachment(request, document)
	if success:
		messages.success(request, _("File has been uploaded successfully!"))
		return HttpResponseRedirect(reverse("information_pages:attachments", args=[document.url_title]))
	else:
		return render(request, "information_pages_attachments.html", {
			'document': document,
			'edit_url': reverse('information_pages:attachments', args=[document.url_title]),
			'form': form,
			'attachments': document.attachments.all().order_by('index'),
			'active_page': 'attachments',
			'permission_warning': permission_warning(request.user, document),
		})
