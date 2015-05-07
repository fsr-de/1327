from . import models


def menu(request):
	menu_items = models.MenuItem.objects.filter(parent_id=None)
	menu_items = [
		menu_item for menu_item in menu_items
		if menu_item.can_view(request.user)
	]

	for item in menu_items:
		mark_selected(request, item)

	return {
		'main_menu': menu_items
	}


def mark_selected(request, menu_item):
	menu_item.submenu = menu_item.children.all()
	menu_item.submenu = [
		submenu_item for submenu_item in menu_item.submenu
		if submenu_item.can_view(request.user)
	]
	for child in menu_item.submenu:
		if mark_selected(request, child):
			menu_item.selected = True
			return True
	current_view = request.resolver_match.view_name
	item_view = menu_item.link
	if current_view == item_view:
		menu_item.selected = True
		return True
	if item_view.startswith('admin:') and current_view.startswith('admin:'):
		menu_item.selected = True
		return True

def can_create_informationpage(request):
	return {'CAN_CREATE_INFORMATIONPAGE': request.user.has_perm("information_pages.add_informationdocument")}
