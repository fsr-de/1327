import re

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.utils.text import slugify as django_slugify
from django.utils.translation import ugettext_lazy as _

from guardian.core import ObjectPermissionChecker

import markdown
from markdown.extensions import Extension
from markdown.extensions.toc import TocExtension


URL_TITLE_REGEX = re.compile(r'^[a-zA-Z0-9-_\/]*$')


def save_main_menu_item_order(main_menu_items, user, parent_id=None):
	from .models import MenuItem
	order_counter = 0

	# check whether we are allowed to change all children of the current level
	# in case we are not allowed to do that, we have to make sure, that we are not altering the original
	# order of the menu items, as we are not allowed to do so.
	all_menu_items_on_this_level = MenuItem.objects.filter(menu_type=MenuItem.MAIN_MENU, parent_id=parent_id)
	menu_item_order_map = {menu_item: menu_item.order for menu_item in all_menu_items_on_this_level if menu_item.can_edit(user)}
	use_old_order = len(menu_item_order_map) != all_menu_items_on_this_level.count()

	for item in main_menu_items:
		item_id = item['id']
		menu_item = MenuItem.objects.get(pk=item_id)
		if menu_item.can_edit(user):
			menu_item.menu_type = MenuItem.MAIN_MENU
			if use_old_order:
				menu_item.order = menu_item_order_map[menu_item]
			else:
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


# see https://pythonhosted.org/Markdown/release-2.6.html#safe_mode-deprecated
class EscapeHtml(Extension):
	def extendMarkdown(self, md, md_globals):
		del md.preprocessors['html_block']
		del md.inlinePatterns['html']


def convert_markdown(text):
	from _1327.documents.markdown_internal_link_extension import InternalLinksMarkdownExtension
	md = markdown.Markdown(extensions=[EscapeHtml(), TocExtension(baselevel=2), InternalLinksMarkdownExtension(), 'markdown.extensions.abbr', 'markdown.extensions.tables'])
	return md.convert(text + abbreviation_explanation_markdown()), md.toc


def slugify(string):
	slug = '/'.join([django_slugify(part) for part in string.split('/')])
	while slug.endswith('/'):
		slug = slug[:-1]
	while '//' in slug:
		slug = slug.replace('//', '/')
	return slug


def find_root_menu_items(items):
	# find root menu items by recursively traversing tree bottom-up
	if len(items) == 0:
		return []

	real_root_items = set()
	questionable_root_items = set()

	for item in items:
		if item.parent is None:
			real_root_items.add(item)
		else:
			questionable_root_items.add(item.parent)

	real_root_items.update(find_root_menu_items(questionable_root_items))
	return real_root_items


def slugify_and_clean_url_title(instance, url_title):
	from _1327.documents.models import Document
	from _1327.shortlinks.models import Shortlink

	if URL_TITLE_REGEX.fullmatch(url_title) is None:
		raise ValidationError(_('Only the following characters are allowed in the URL: a-z, A-Z, 0-9, -, _, /'))
	url_title = slugify(url_title)

	if any(url_part in settings.FORBIDDEN_URLS for url_part in url_title.split('/')):
		raise ValidationError(_('The URL contains parts that are not allowed in custom URLs.'))
	if not instance.url_title == url_title:
		if Document.objects.filter(url_title=url_title).exists():
			raise ValidationError(_('This URL is already taken.'))
		if Shortlink.objects.filter(url_title=url_title).exists():
			raise ValidationError(_('This URL is already taken.'))
	return url_title


def document_permission_overview(user, document):
	can_edit = user.has_perm(document.edit_permission_name, document)
	if not can_edit:
		return []

	main_groups = [
		settings.ANONYMOUS_GROUP_NAME,
		settings.UNIVERSITY_GROUP_NAME,
		settings.STUDENT_GROUP_NAME,
		settings.STAFF_GROUP_NAME,
	]
	permissions = []
	for group_name in main_groups:
		group = Group.objects.get(name=group_name)
		checker = ObjectPermissionChecker(group)
		checker.prefetch_perms([document])
		if checker.has_perm(document.edit_permission_name, document):
			permissions.append((group.name, "edit"))
		elif checker.has_perm(document.view_permission_name, document):
			permissions.append((group.name, "view"))
		else:
			permissions.append((group.name, "none"))

	for group in Group.objects.exclude(name__in=main_groups):
		checker = ObjectPermissionChecker(group)
		checker.prefetch_perms([document])
		if checker.has_perm(document.edit_permission_name, document):
			permissions.append((group.name, "edit"))
		elif checker.has_perm(document.view_permission_name, document):
			permissions.append((group.name, "view"))

	return permissions
