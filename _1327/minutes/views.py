from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.http import HttpResponseRedirect, HttpResponse
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from django.forms.formsets import formset_factory
from guardian.shortcuts import get_perms
from guardian.models import Group
import markdown
from markdown.extensions.toc import TocExtension
from datetime import datetime

from _1327.documents.utils import handle_edit, prepare_versions, handle_autosave, handle_attachment, delete_old_empty_pages
from _1327.documents.models import Document
from _1327.documents.forms import PermissionForm
from _1327.user_management.shortcuts import get_object_or_error
from .models import MinutesDocument


@login_required
def list(request):
	years = {}
	minutes = MinutesDocument.objects.order_by('-date')
	for m in minutes:
		if not request.user.has_perm(m, MinutesDocument.get_view_permission()):
			continue

		if m.date.year not in years:
			years[m.date.year] = []
		years[m.date.year].append(m)
	new_years = [{'year': year, 'minutes': minutes} for (year, minutes) in years.items()]
	new_years = sorted(new_years, key=lambda x: x['year'], reverse=True)
	return render(request, "minutes_list.html", {
		'years': new_years,
	})


def create(request):
	if request.user.has_perm("information_pages.add_informationdocument"):
		delete_old_empty_pages()
		title = _("New minutes document from {}").format(str(datetime.now()))
		url_title = slugify(title)
		MinutesDocument.objects.get_or_create(author=request.user, url_title=url_title, title=title, moderator=request.user)
		new_autosaved_pages = None#get_new_autosaved_pages_for_user(request.user);
		return edit(request, url_title)#, new_autosaved_pages)
	else:
		return HttpResponseForbidden()


def edit(request, title):
	document = get_object_or_error(MinutesDocument, request.user, ['minutes.change_minutesdocument'], url_title=title)
	success, form = handle_edit(request, document)
	if success:
		messages.success(request, _("Successfully saved changes"))
		return HttpResponseRedirect(reverse('minutes:view', args=[document.url_title]))
	else:
		return render(request, "minutes_edit.html", {
			'document': document,
			'edit_url': reverse('minutes:edit', args=[document.url_title]),
			'form': form,
			'active_page': 'edit',
		})


def autosave(request, title):
	document = None
	try:
		document = get_object_or_error(MinutesDocument, request.user, ['minutes.change_minutesdocument'], url_title=title)
	except Document.DoesNotExist:
		pass

	handle_autosave(request, document)
	return HttpResponse()


def versions(request, title):
	# get all versions of the document
	document = get_object_or_error(MinutesDocument, request.user, ['minutes.change_minutesdocument'], url_title=title)
	document_versions = prepare_versions(document)

	return render(request, 'minutes_versions.html', {
		'active_page': 'versions',
		'versions': document_versions,
		'document': document,
	})


def view(request, title):
	document = get_object_or_error(MinutesDocument, request.user, [MinutesDocument.get_view_permission()], url_title=title)

	md = markdown.Markdown(safe_mode='escape', extensions=[TocExtension(baselevel=2)])
	text = md.convert(document.text)

	return render(request, 'minutes_base.html', {
		'document': document,
		'text': text,
		'toc': md.toc,
		'attachments': document.attachments.all().order_by('index'),
		'active_page': 'view',
	})


def permissions(request, title):
	document = get_object_or_error(MinutesDocument, request.user, ['minutes.change_minutesdocument'], url_title=title)

	permissionFS = formset_factory(form=PermissionForm, extra=0)
	groups = Group.objects.all()

	initial_data = []
	for group in groups:
		group_permissions = get_perms(group, document)
		data = {
			"change_permission": "change_minutesdocument" in group_permissions,
			"delete_permission": "delete_minutesdocument" in group_permissions,
			"view_permission": MinutesDocument.VIEW_PERMISSION_NAME in group_permissions,
			"group_name": group.name,
		}
		initial_data.append(data)

	formset = permissionFS(request.POST or None, initial=initial_data)
	if request.POST and formset.is_valid():
		for form in formset:
			form.save(document)
		messages.success(request, _("Permissions have been changed successfully."))

		return HttpResponseRedirect(reverse('minutes:permissions', args=[document.url_title]))

	return render(request, 'minutes_permissions.html', {
		'document': document,
		'formset': formset,
		'active_page': 'permissions',
	})


def attachments(request, title):
	document = get_object_or_error(MinutesDocument, request.user, ['minutes.change_minutesdocument'], url_title=title)

	success, form = handle_attachment(request, document)
	if success:
		messages.success(request, _("File has been uploaded successfully!"))
		return HttpResponseRedirect(reverse("minutes:attachments", args=[document.url_title]))
	else:
		return render(request, "minutes_attachments.html", {
			'document': document,
			'edit_url': reverse('minutes:attachments', args=[document.url_title]),
			'form': form,
			'attachments': document.attachments.all().order_by('index'),
			'active_page': 'attachments',
		})
