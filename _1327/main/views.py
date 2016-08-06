import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.core.urlresolvers import reverse
from django.forms import formset_factory
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_POST

import markdown
from markdown.extensions.toc import TocExtension

from _1327.documents.models import Document
from _1327.documents.utils import permission_warning
from _1327.main.forms import get_permission_form

from .forms import MenuItemForm
from .models import MenuItem
from .utils import save_footer_item_order, save_main_menu_item_order


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
	main_menu_items = []
	footer_items = []

	items = [item for item in MenuItem.objects.filter(menu_type=MenuItem.MAIN_MENU, parent=None).order_by('order') if item.can_view_in_list(request.user)]
	for item in items:
		subitems = MenuItem.objects.filter(menu_type=MenuItem.MAIN_MENU, parent=item).order_by('order')
		if subitems:
			for subitem in subitems:
				subsubitems = MenuItem.objects.filter(menu_type=MenuItem.MAIN_MENU, parent=subitem).order_by('order')
				if subsubitems:
					subitem.subitems = subsubitems
			item.subitems = subitems
		main_menu_items.append(item)

	if request.user.is_superuser:  # only allow editing of footer items for superusers
		for item in MenuItem.objects.filter(menu_type=MenuItem.FOOTER, parent=None).order_by('order'):
			footer_items.append(item)

	return render(request, 'menu_items_index.html', {
		'main_menu_items': main_menu_items,
		'footer_items': footer_items
	})


def menu_item_create(request):
	form = MenuItemForm(request.POST or None, instance=MenuItem())
	if form.is_valid():
		form.save()
		messages.success(request, _("Successfully created menu item."))
		return redirect('menu_items_index')
	else:
		return render(request, 'menu_item_edit.html', {'form': form})


def menu_item_edit(request, menu_item_pk):
	menu_item = MenuItem.objects.get(pk=menu_item_pk)
	if not menu_item.can_edit(request.user):
		raise PermissionDenied
	form = MenuItemForm(request.POST or None, instance=menu_item)

	PermissionForm = get_permission_form(menu_item)
	PermissionFormset = formset_factory(get_permission_form(menu_item), extra=0)

	content_type = ContentType.objects.get_for_model(menu_item)
	initial_data = PermissionForm.prepare_initial_data(Group.objects.all(), content_type, menu_item)
	formset = PermissionFormset(request.POST or None, initial=initial_data)

	if form.is_valid() and request.POST and formset.is_valid():
		form.save()
		for permission_form in formset:
			permission_form.save(menu_item)
		messages.success(request, _("Successfully edited menu item."))
		return redirect('menu_items_index')
	return render(request, 'menu_item_edit.html', {
		'form': form,
		'formset_header': PermissionForm.header(content_type),
		'formset': formset,
	})


@require_POST
def menu_item_delete(request):
	menu_item_id = request.POST.get("item_id")
	menu_item = MenuItem.objects.get(pk=menu_item_id)
	if not menu_item.can_delete(request.user):
		raise PermissionDenied
	menu_item.delete()
	return HttpResponse()


@require_POST
def menu_items_update_order(request):
	body_unicode = request.body.decode('utf-8')
	data = json.loads(body_unicode)
	main_menu_items = data['main_menu_items']
	footer_items = data['footer_items']
	if len(main_menu_items) == 0:
		messages.error(request, _("There must always be at least one item in the main menu."))
	elif len(footer_items) == 0:
		messages.error(request, _("There must always be at least one item in the footer menu."))
	else:
		save_main_menu_item_order(main_menu_items)
		save_footer_item_order(footer_items)
	return HttpResponse()
