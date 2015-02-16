from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.http import HttpResponseRedirect, HttpResponse
from django.utils.translation import ugettext_lazy as _

from _1327.user_management.decorators import admin_required
from _1327.documents.utils import handle_edit, handle_autosave, prepare_versions
from _1327.documents.models import Document


@admin_required
def edit(request, title):
	document = get_object_or_404(Document, url_title=title, type='I')
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

@admin_required
def autosave(request, title):
	document = None
	try:
		document = Document.objects.get(url_title=title, type='I')
	except Document.DoesNotExist:
		pass

	handle_autosave(request, document)
	return HttpResponse()

@admin_required
def versions(request, title):
	# get all versions of the document
	document = get_object_or_404(Document, url_title=title, type='I')
	document_versions = prepare_versions(document)

	return render(request, 'information_pages_versions.html', {
		'active_page': 'versions',
		'versions': document_versions,
		'document': document,
	})


def view_information(request, title):
	document = get_object_or_404(Document, url_title=title, type='I')

	return render(request, 'information_pages_base.html', {
		'document': document,
		'active_page': 'view',
	})
