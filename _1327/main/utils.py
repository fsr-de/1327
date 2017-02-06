from django.utils.text import slugify as django_slugify


def save_main_menu_item_order(main_menu_items, user, parent_id=None):
	from .models import MenuItem
	order_counter = 0
	for item in main_menu_items:
		item_id = item['id']
		menu_item = MenuItem.objects.get(pk=item_id)
		if menu_item.can_edit(user):
			menu_item.menu_type = MenuItem.MAIN_MENU
			menu_item.order = order_counter
			order_counter += 1
			if parent_id:
				parent = MenuItem.objects.get(pk=parent_id)
			else:
				parent = None
			if user.is_superuser or (parent and parent.can_view_in_list(user)):  # check that the item is moved under a parent where the change_children permission is set
				menu_item.parent = parent
			menu_item.save()
		if 'children' in item:
			save_main_menu_item_order(item['children'], user, item_id)


def save_footer_item_order(footer_items, user, order_counter=0):
	from .models import MenuItem
	for item in footer_items:
		item_id = item['id']
		menu_item = MenuItem.objects.get(pk=item_id)
		if menu_item.can_edit(user):
			menu_item.menu_type = MenuItem.FOOTER
			menu_item.order = order_counter
			order_counter += 1
			menu_item.parent = None
			menu_item.save()
		# in case subitems have been moved into the footer save them as well, remove parents but keep their order
		if 'children' in item:
			order_counter = save_footer_item_order(item['children'], user, order_counter)
	return order_counter


def abbreviation_explanation_markdown():
	from .models import AbbreviationExplanation
	return "\n" + ("\n".join([str(abbr) for abbr in AbbreviationExplanation.objects.all()]))


def slugify(string):
	return '/'.join([django_slugify(part) for part in string.split('/')])


def find_root_menu_items(items):
	# find root menu items by recursively traversing tree bottom-up
	if len(items) == 0:
		return []

	real_root_items = []
	questionable_root_items = set()

	for item in items:
		if item.parent is None:
			real_root_items.append(item)
		else:
			questionable_root_items.add(item.parent)

	real_root_items.extend(find_root_menu_items(questionable_root_items))
	return real_root_items
