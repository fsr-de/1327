from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.http import HttpResponseRedirect, HttpResponse
from django.utils.translation import ugettext_lazy as _
from django.forms.formsets import formset_factory
from guardian.decorators import permission_required_or_403
from guardian.shortcuts import get_perms
from guardian.models import Group

from _1327.documents.utils import handle_edit, prepare_versions, handle_autosave
from _1327.documents.models import Document
from _1327.documents.forms import PermissionForm
from _1327.information_pages.models import InformationDocument
from _1327.user_management.shortcuts import get_object_or_error


def edit(request, title):
	document = get_object_or_error(InformationDocument, request.user, ['information_pages.change_informationdocument'], url_title=title)
	success, form = handle_edit(request, document)
	if success:
		messages.success(request, _("Successfully saved changes"))
		return HttpResponseRedirect(reverse('information_pages:edit', args=[document.url_title]))
	else:
		return render(request, "information_pages_edit.html", {
			'document': document,
			'edit_url': reverse('information_pages:edit', args=[document.url_title]),
			'form': form,
			'active_page': 'edit',
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
	})


def view_information(request, title):
	document = get_object_or_error(InformationDocument, request.user, [InformationDocument.get_view_permission()], url_title=title)

	return render(request, 'information_pages_base.html', {
		'document': document,
		'active_page': 'view',
	})


def permissions(request, title):
	document = get_object_or_error(InformationDocument, request.user, ['information_pages.change_informationdocument'], url_title=title)

	permissionFS = formset_factory(form=PermissionForm, extra=0)
	groups = Group.objects.all()

	initial_data = []
	for group in groups:
		group_permissions = get_perms(group, document)
		data = {
			"change_permission": "change_informationdocument" in group_permissions,
			"delete_permission": "delete_informationdocument" in group_permissions,
			"view_permission": InformationDocument.VIEW_PERMISSION_NAME in group_permissions,
			"group_name": group.name,
		}
		initial_data.append(data)

	formset = permissionFS(request.POST or None, initial=initial_data)
	if request.POST and formset.is_valid():
		for form in formset:
			form.save(document)
		messages.success(request, _("Permissions have been changed successfully."))

		return HttpResponseRedirect(reverse('information_pages:permissions', args=[document.url_title]))

	return render(request, 'information_pages_permissions.html', {
		'document': document,
		'formset': formset,
		'active_page': 'permissions',
	})
