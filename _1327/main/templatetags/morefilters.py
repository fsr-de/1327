from django.template import Library
from django.template.defaultfilters import floatformat

register = Library()


@register.filter(name='percentage')
def percentage(value):
	if value is None:
		return None
	return floatformat(value, 1) + '%'


@register.filter(name='can_edit_menu_item')
def can_edit_menu_item(menu_item, user):
	return menu_item.can_edit(user)


@register.filter(name='can_delete_menu_item')
def can_delete_menu_item(menu_item, user):
	return menu_item.can_delete(user)


@register.filter(name='can_view_menu_item')
def can_view_menu_item(menu_item, user):
	return menu_item.can_view(user)


@register.filter(name='sort_users_by_name')
def sort_users_by_name(users):
	return sorted(users, key=lambda user: ((user.last_name or "").lower(), (user.first_name or "").lower(), (user.get_full_name() or "").lower()))


@register.filter(name='permission_filter')
def permission_filter(permission_overview, permission_name):
	return [group for group, permission in permission_overview if permission == permission_name]
