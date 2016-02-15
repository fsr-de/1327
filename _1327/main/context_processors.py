from . import models


def menu(request):
	main_menu = models.MenuItem.objects.filter(title="Main Menu").first()
	menu_items = models.MenuItem.objects.filter(parent_id=main_menu)
	menu_items = [menu_item for menu_item in menu_items if menu_item.can_view(request.user)]

	for item in menu_items:
		mark_selected(request, item)

	footer = models.MenuItem.objects.filter(title="Footer").first()
	footer_items = models.MenuItem.objects.filter(parent_id=footer)
	footer_items = [footer_item for footer_item in footer_items if footer_item.can_view(request.user)]

	for item in footer_items:
		mark_selected(request, item)

	return {
		'main_menu': menu_items,
		'footer': footer_items,
	}


def mark_selected(request, menu_item):
	menu_item.submenu = menu_item.children.all()
	menu_item.submenu = [submenu_item for submenu_item in menu_item.submenu if submenu_item.can_view(request.user)]
	for child in menu_item.submenu:
		if mark_selected(request, child):
			menu_item.selected = True
			return True

	current_view = request.resolver_match
	if current_view is not None:
		current_view_name = current_view.view_name
		if menu_item.link:
			item_view = menu_item.link
			if current_view_name == item_view:
				menu_item.selected = True
				return True
			if item_view.startswith('admin:') and current_view_name.startswith('admin:'):
				menu_item.selected = True
				return True
		elif menu_item.document:
			if 'title' in request.resolver_match.kwargs and menu_item.document.url_title == request.resolver_match.kwargs['title']:
				menu_item.selected = True
				return True


def can_create_informationpage(request):
	return {'CAN_CREATE_INFORMATIONPAGE': request.user.has_perm("information_pages.add_informationdocument")}


def can_create_minutes(request):
	return {'CAN_CREATE_MINUTES': request.user.has_perm("minutes.add_minutesdocument")}


def can_create_poll(request):
	return {'CAN_CREATE_POLL': request.user.has_perm("polls.add_poll")}
