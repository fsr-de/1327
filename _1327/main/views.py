from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.utils.translation import ugettext_lazy as _

import markdown
from markdown.extensions.toc import TocExtension

from _1327.documents.models import Document
from _1327.documents.utils import permission_warning

from .forms import MenuItemForm
from .models import MenuItem


def index(request):
	try:
		document = Document.objects.get(id=settings.MAIN_PAGE_ID)
		return HttpResponseRedirect(reverse('documents:view', args=[document.url_title]))

		md = markdown.Markdown(safe_mode='escape', extensions=[TocExtension(baselevel=2)])
		text = md.convert(document.text)

		template = 'information_pages_base.html' if document.polymorphic_ctype.model == 'informationdocument' else 'minutes_base.html'
		return render(request, template, {
			'document': document,
			'text': text,
			'toc': md.toc,
			'attachments': document.attachments.filter(no_direct_download=False).order_by('index'),
			'active_page': 'view',
			'permission_warning': permission_warning(request.user, document),
		})
	except ObjectDoesNotExist:
		# nobody created a mainpage yet -> show default main page
		return render(request, 'index.html')


def menu_items_index(request):
	menu_items = MenuItem.objects.all()  # TODO (#268): get only items that can be edited by the current user
	return render(request, 'menu_items_index.html', {'menu_items': menu_items})


def menu_item_create(request):
	form = MenuItemForm(request.POST or None, instance=MenuItem())
	if form.is_valid():
		form.save()
		messages.success(request, _("Successfully created menu item."))
		return redirect('menu_items_index')
	else:
		return render(request, 'menu_item_edit.html', {'form': form})


def menu_item_edit(request, menu_item_pk):
	menu_item = MenuItem.objects.get(pk=menu_item_pk)  # TODO (#268): check permission to edit
	form = MenuItemForm(request.POST or None, instance=menu_item)
	if form.is_valid():
		form.save()
		messages.success(request, _("Successfully edited menu item."))
		return redirect('menu_items_index')
	return render(request, 'menu_item_edit.html', {'form': form})


def menu_item_delete(request, menu_item_pk):
	menu_item = MenuItem.objects.get(pk=menu_item_pk)  # TODO (#268): check permission to delete
	menu_item.delete()
	messages.success(request, _("The menu item was deleted successfully."))
	return redirect('menu_items_index')
