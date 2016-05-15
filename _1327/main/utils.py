from .models import MenuItem


def save_main_menu_item_order(main_menu_items, parent_id=None):
	order_counter = 0
	for item in main_menu_items:
		item_id = item['id']
		menu_item = MenuItem.objects.get(pk=item_id)  # TODO: check permission to edit
		menu_item.menu_type = MenuItem.MAIN_MENU
		menu_item.order = order_counter
		order_counter += 1
		if parent_id:
			menu_item.parent = MenuItem.objects.get(pk=parent_id)
		else:
			menu_item.parent = None
		menu_item.save()
		if 'children' in item:
			save_main_menu_item_order(item['children'], item_id)


def save_footer_item_order(footer_items, order_counter=0):
	for item in footer_items:
		item_id = item['id']
		menu_item = MenuItem.objects.get(pk=item_id)  # TODO: check permission to edit
		menu_item.menu_type = MenuItem.FOOTER
		menu_item.order = order_counter
		order_counter += 1
		menu_item.parent = None
		menu_item.save()
		# in case subitems have been moved into the footer save them as well, remove parents but keep their order
		if 'children' in item:
			order_counter = save_footer_item_order(item['children'], order_counter)
	return order_counter
