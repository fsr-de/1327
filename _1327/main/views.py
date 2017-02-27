import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.core.urlresolvers import reverse
from django.forms import formset_factory, modelformset_factory
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, Http404, redirect, render
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_POST
from guardian.shortcuts import get_objects_for_user

import markdown
from markdown.extensions.toc import TocExtension

from _1327.documents.models import Document
from _1327.documents.views import edit as document_edit, view as document_view
from _1327.main.forms import AbbreviationExplanationForm, get_permission_form
from _1327.main.models import AbbreviationExplanation
from _1327.main.utils import abbreviation_explanation_markdown, document_permission_overview, find_root_menu_items
from _1327.shortlinks.models import Shortlink
from _1327.shortlinks.views import edit as shortlink_edit, view as shortlink_view
from .forms import MenuItemAdminForm, MenuItemCreationAdminForm, MenuItemCreationForm, MenuItemForm
from .models import MenuItem
from .utils import save_footer_item_order, save_main_menu_item_order


def index(request):
	try:
		document = Document.objects.get(id=settings.MAIN_PAGE_ID)
		return HttpResponseRedirect(reverse(document.get_view_url_name(), args=[document.url_title]))

		md = markdown.Markdown(safe_mode='escape', extensions=[TocExtension(baselevel=2), 'markdown.extensions.abbr', 'markdown.extensions.tables'])
		text = md.convert(document.text + abbreviation_explanation_markdown())

		template = 'information_pages_base.html' if document.polymorphic_ctype.model == 'informationdocument' else 'minutes_base.html'
		return render(request, template, {
			'document': document,
			'text': text,
			'toc': md.toc,
			'attachments': document.attachments.filter(no_direct_download=False).order_by('index'),
			'active_page': 'view',
			'view_page': True,
			'permission_overview': document_permission_overview(request.user, document),
		})
	except ObjectDoesNotExist:
		# nobody created a mainpage yet -> show default main page
		return render(request, 'index.html')


def view(request, title):
	if Document.objects.filter(url_title=title).exists():
		return document_view(request, title)
	if Shortlink.objects.filter(url_title=title).exists():
		return shortlink_view(request, title)
	raise Http404


def edit(request, title):
	if Document.objects.filter(url_title=title).exists():
		return document_edit(request, title)
	if Shortlink.objects.filter(url_title=title).exists():
		return shortlink_edit(request, title)
	raise Http404


def menu_items_index(request):
	if not request.user.is_superuser and len(get_objects_for_user(request.user, MenuItem.CHANGE_CHILDREN_PERMISSION_NAME, klass=MenuItem)) == 0:
		raise PermissionDenied

	main_menu_items = []
	footer_items = []

	items = find_root_menu_items(
		[item for item in MenuItem.objects.filter(menu_type=MenuItem.MAIN_MENU, children=None).order_by('order') if item.can_view_in_list(request.user)]
	)

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
	if request.user.is_superuser:
		form = MenuItemCreationAdminForm(request.user, request.POST or None, instance=MenuItem())
	else:
		form = MenuItemCreationForm(request.user, request.POST or None, instance=MenuItem())

	if form.is_valid():
		menu_item = form.save()
		menu_item.set_all_permissions(form.cleaned_data['group'])
		messages.success(request, _("Successfully created menu item."))
		return redirect('menu_items_index')
	else:
		return render(request, 'menu_item_edit.html', {'form': form})


def menu_item_edit(request, menu_item_pk):
	menu_item = get_object_or_404(MenuItem, pk=menu_item_pk)
	if not menu_item.can_edit(request.user):
		raise PermissionDenied
	if request.user.is_superuser:
		form = MenuItemAdminForm(request.POST or None, instance=menu_item)
	else:
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
	menu_item = get_object_or_404(MenuItem, pk=menu_item_id)
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
	if request.user.is_superuser:
		if len(main_menu_items) == 0:
			messages.error(request, _("There must always be at least one item in the main menu."))
		elif len(footer_items) == 0:
			messages.error(request, _("There must always be at least one item in the footer menu."))
		else:
			save_main_menu_item_order(main_menu_items, request.user)
			save_footer_item_order(footer_items, request.user)
	else:
		save_main_menu_item_order(main_menu_items, request.user)
	return HttpResponse()


def abbreviation_explanation_edit(request):
	if not request.user.is_superuser:
		raise PermissionDenied

	abbrs = AbbreviationExplanation.objects.order_by('abbreviation')

	AbbreviationExplanationFormset = modelformset_factory(AbbreviationExplanation, form=AbbreviationExplanationForm, can_delete=True, extra=1)
	formset = AbbreviationExplanationFormset(request.POST or None, queryset=abbrs)

	if formset.is_valid():
		formset.save()
		messages.success(request, _("Successfully updated the abbreviation explanations."))
		return redirect('abbreviation_explanation')
	else:
		return render(request, "abbreviation_explanation.html", dict(formset=formset))
