from . import models


def menu(request):
	menu_items = models.MenuItem.objects.filter(parent_id=None)

	for item in menu_items:
		mark_selected(request, item)

	return {
		'main_menu': menu_items
	}


def mark_selected(request, menu_item):
	menu_item.submenu = menu_item.children.all()
	for child in menu_item.submenu:
		if mark_selected(request, child):
			menu_item.selected = True
			return True
	current_view = request.resolver_match.view_name
	item_view = menu_item.link
	if current_view == item_view:
		menu_item.selected = True
		return True
