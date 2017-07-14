from collections import namedtuple

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from guardian.shortcuts import assign_perm

from _1327.documents.models import Document

MENUITEM_VIEW_PERMISSION_NAME = 'view_menuitem'
MENUITEM_EDIT_PERMISSION_NAME = 'change_menuitem'
MENUITEM_CHANGE_CHILDREN_PERMISSION_NAME = 'changechildren_menuitem'

NamedPermission = namedtuple('NamedPermission', ['name', 'description'])


class MenuItem(models.Model):
	MAIN_MENU = 1
	FOOTER = 2
	MENU_TYPES = (
		(MAIN_MENU, _("Main Menu")),
		(FOOTER, _("Footer")),
	)
	title = models.CharField(max_length=255, unique=False, verbose_name=_("Title"))
	order = models.IntegerField(default=999)

	link = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Link"))

	document = models.ForeignKey(Document, blank=True, null=True, on_delete=models.PROTECT, verbose_name=_("Document"), related_name='menu_items')

	parent = models.ForeignKey('self', blank=True, null=True, on_delete=models.CASCADE, related_name='children')

	menu_type = models.IntegerField(choices=MENU_TYPES, default=MAIN_MENU)

	VIEW_PERMISSION_NAME = MENUITEM_VIEW_PERMISSION_NAME
	EDIT_PERMISSION_NAME = MENUITEM_EDIT_PERMISSION_NAME
	CHANGE_CHILDREN_PERMISSION_NAME = MENUITEM_CHANGE_CHILDREN_PERMISSION_NAME

	class Meta:
		ordering = ['order']
		permissions = (
			(MENUITEM_VIEW_PERMISSION_NAME, 'User/Group is allowed to view this menu item'),
			(MENUITEM_CHANGE_CHILDREN_PERMISSION_NAME, 'User/Group is allowed to change children items'),
		)

	def __str__(self):
		return self.title

	def get_url(self):
		if self.link:
			split = self.link.split("?")
			if len(split) == 1:
				return reverse(split[0])
			else:
				key, value = split[1].split('=')
				return reverse(split[0], kwargs={key: value})
		elif self.document:
			return self.document.get_view_url()
		else:
			return "#"

	@property
	def view_permission_name(self):
		content_type = ContentType.objects.get_for_model(self)
		return "{app}.view_{model}".format(app=content_type.app_label, model=content_type.model)

	@property
	def change_children_permission_name(self):
		content_type = ContentType.objects.get_for_model(self)
		return "{app}.changechildren_{model}".format(app=content_type.app_label, model=content_type.model)

	@property
	def edit_permission_name(self):
		content_type = ContentType.objects.get_for_model(self)
		return "{app}.change_{model}".format(app=content_type.app_label, model=content_type.model)

	def can_view(self, user):
		permission_name = self.view_permission_name
		return user.has_perm(permission_name, self) or user.has_perm(permission_name)

	def can_view_in_list(self, user):
		return self.can_edit(user) or user.has_perm(self.change_children_permission_name, self)

	def can_edit(self, user):
		change_children_permission_name = self.change_children_permission_name
		edit_permission_name = self.edit_permission_name
		if user.has_perm(change_children_permission_name, self.parent) or user.has_perm(change_children_permission_name):
			return True
		elif user.has_perm(edit_permission_name, self) or user.has_perm(edit_permission_name):
			return True
		elif self.parent and self.parent.parent:
			return user.has_perm(change_children_permission_name, self.parent.parent)
		return False

	def can_delete(self, user):
		return self.can_edit(user)

	def set_all_permissions(self, user_or_group):
		assign_perm(self.view_permission_name, user_or_group, self)
		assign_perm(self.change_children_permission_name, user_or_group, self)

	@classmethod
	def used_permissions(cls):
		app_label = ContentType.objects.get_for_model(cls).app_label
		return (
			NamedPermission(name="{app}.{codename}".format(app=app_label, codename=cls.VIEW_PERMISSION_NAME), description=_('view')),
			NamedPermission(name="{app}.{codename}".format(app=app_label, codename=cls.CHANGE_CHILDREN_PERMISSION_NAME), description=_('change children')),
			NamedPermission(name="{app}.{codename}".format(app=app_label, codename=cls.EDIT_PERMISSION_NAME), description=_('edit')),
		)


class AbbreviationExplanation(models.Model):

	abbreviation = models.CharField(max_length=255, unique=True, verbose_name=_("Abbreviation"))
	explanation = models.CharField(max_length=255, blank=False, null=False, verbose_name=_("Explanation"))

	def __str__(self):
		return '*[' + self.abbreviation + ']: ' + self.explanation
