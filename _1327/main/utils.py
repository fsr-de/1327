import re

import bleach

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.utils.text import slugify as django_slugify
from django.utils.translation import gettext_lazy as _

from guardian.core import ObjectPermissionChecker

import markdown
from markdown.extensions import Extension
from markdown.extensions.toc import TocExtension
from markdown.postprocessors import Postprocessor


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
		if (menu_item.link or menu_item.document) and 'children' in item:
			continue
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


# Most of the tags / attributes are for normal markdown
# (see here: https://daringfireball.net/projects/markdown/syntax).
# The abbr tag and its attribute are for the `abbr` extension.
# The div tag, its attribute, and the attributes of the h tags are for the `toc` extension.
# The table, thead, tr, th, tbody, td tags and the attributes of td and th are for the `tables` extension.
ALLOWED_TAGS = [
	'p', 'br', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'ol',
	'ul', 'li', 'code', 'pre', 'hr', 'a', 'em', 'strong', 'img',
	'abbr', 'div',
	'table', 'thead', 'tr', 'th', 'tbody', 'td',
]
ALLOWED_ATTRIBUTES = {
	'a': ['title', 'href'],
	'img': ['alt', 'src', 'title', 'width', 'height'],
	'abbr': ['title'],
	'div': ['class'],
	'h1': ['id'], 'h2': ['id'], 'h3': ['id'], 'h4': ['id'], 'h5': ['id'], 'h6': ['id'],
	'td': ['align'], 'th': ['align'],
}
ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']


class BleachPostprocessor(Postprocessor):
	def run(self, text):
		return bleach.clean(text, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, protocols=ALLOWED_PROTOCOLS)


# see https://python-markdown.github.io/change_log/release-2.6/#safe_mode-deprecated
class EscapeHtml(Extension):
	def extendMarkdown(self, md):
		md.preprocessors.deregister('html_block')
		md.inlinePatterns.deregister('html')
		md.postprocessors.register(BleachPostprocessor(), 'bleach', -1000)


def convert_markdown(text):
	from _1327.documents.markdown_internal_link_extension import InternalLinksMarkdownExtension
	md = markdown.Markdown(
		extensions=[
			EscapeHtml(),
			TocExtension(baselevel=2),
			InternalLinksMarkdownExtension(),
			'_1327.minutes.markdown_minutes_extensions',
			'_1327.documents.markdown_scaled_image_extension',
			'markdown.extensions.abbr',
			'markdown.extensions.tables',
		],
		output_format='html5'
	)
	return md.convert(text + abbreviation_explanation_markdown()), bleach.clean(md.toc, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, protocols=ALLOWED_PROTOCOLS)


def slugify(string):
	slug = '/'.join([django_slugify(part) for part in string.split('/')])
	while slug.endswith('/'):
		slug = slug[:-1]
	while '//' in slug:
		slug = slug.replace('//', '/')
	return slug


class SlugWithSlashConverter:
	regex = r'[\w\-/]+'

	def to_python(self, value):
		return str(value)

	def to_url(self, value):
		return str(value)


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


def email_belongs_to_domain(email, domain):
	return email.rpartition('@')[2] == domain


def replace_email_domain(email, original_domain, new_domain):
	return email[:-len(original_domain)] + new_domain


def toggle_institution(email):
	for original_domain, new_domain in settings.INSTITUTION_EMAIL_REPLACEMENTS:
		if email_belongs_to_domain(email, original_domain):
			yield replace_email_domain(email, original_domain, new_domain)
		elif email_belongs_to_domain(email, new_domain):
			yield replace_email_domain(email, new_domain, original_domain)


def alternative_emails(email):
	yield from toggle_institution(email)
	for current_domain, alumni_domain in settings.ALUMNI_EMAIL_REPLACEMENTS:
		if email_belongs_to_domain(email, current_domain):
			alumni_mail = replace_email_domain(email, current_domain, alumni_domain)
			yield alumni_mail
			yield from toggle_institution(alumni_mail)


def clean_email(email):
	if email:
		# Replace email domains in case there are multiple alias domains used in the organisation and all emails should
		# have the same domain.
		for original_domain, new_domain in settings.INSTITUTION_EMAIL_REPLACEMENTS:
			if email_belongs_to_domain(email, original_domain):
				return replace_email_domain(email, original_domain, new_domain)
	return email
