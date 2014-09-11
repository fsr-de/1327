from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _

from _1327.main.decorators import admin_required
from _1327.information_pages.forms import TextForm
from _1327.information_pages.models import Document


@admin_required
def edit(request, title):

	context = RequestContext(request)
	document = get_object_or_404(Document, url_title=title)
	if request.method == 'POST':
		form = TextForm(request.POST)
		if form.is_valid():
			cleaned_data = form.cleaned_data

			document.text = cleaned_data['text']
			document.type = cleaned_data['type']
			document.author = request.user
			if document.title != cleaned_data['title']:
				# if the user changed the title we have to delete the old version 
				# because the url_title will change, too...
				document.title = cleaned_data['title']
				new_document = Document(title=document.title,
										text=document.text,
										type=document.type,
										author=document.author, )
				document.delete()
				document = new_document
			document.save()
			messages.success(request, _("Successfully saved changes"))
			return HttpResponseRedirect(reverse('information_pages:edit', args=[document.url_title]))
		else:
			context['errors'] = form.errors
			context['form'] = form
	else:
		form_data = {
			'title': document.title,
			'text': document.text,
			'type': document.type,
		}
		context['form'] = TextForm(form_data)

	context['document'] = document
	context['edit_url'] = reverse('information_pages:edit', args=[document.url_title])
	context['active_page'] = 'edit'

	return render_to_response("information_pages_edit.html", context_instance=context)

def view_information(request, title):

	document = get_object_or_404(Document, url_title=title)

	context = RequestContext(request)
	context['document'] = document
	context['active_page'] = 'view'

	return render_to_response('information_pages_base.html', context_instance=context)
