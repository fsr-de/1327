from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _

from _1327.main.decorators import admin_required
from _1327.documents.utils import handle_edit, prepare_versions
from _1327.documents.models import Document


@admin_required
def edit(request, title):
	document = get_object_or_404(Document, url_title=title, type='I')
	success, form = handle_edit(request, document)
	if success:
		messages.success(request, _("Successfully saved changes"))
		return HttpResponseRedirect(reverse('information_pages:edit', args=[document.url_title]))
	else:
		return render_to_response("information_pages_edit.html", {
			'document': document,
			'edit_url': reverse('information_pages:edit', args=[document.url_title]),
			'form': form,
			'active_page': 'edit',
		}, context_instance=RequestContext(request))

@admin_required
def versions(request, title):
	# get all versions of the document
	document = get_object_or_404(Document, url_title=title, type='I')
	context = prepare_versions(request, document)
	context['active_page'] = 'versions'

	return render_to_response('information_pages_versions.html', context_instance=context)


def view_information(request, title):
	document = get_object_or_404(Document, url_title=title, type='I')

	context = RequestContext(request)
	context['document'] = document
	context['active_page'] = 'view'

	return render_to_response('information_pages_base.html', context_instance=context)
