from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.translation import ugettext_lazy as _

from _1327.documents.models import Document

MENUITEM_VIEW_PERMISSION_NAME = 'view_menuitem'
MENUITEM_CHANGE_CHILDREN_PERMISSION_NAME = 'changechildren_menuitem'


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
	document = models.ForeignKey(Document, blank=True, null=True, verbose_name=_("Document"))

	parent = models.ForeignKey('self', blank=True, null=True, related_name='children')

	menu_type = models.IntegerField(choices=MENU_TYPES, default=MAIN_MENU)

	VIEW_PERMISSION_NAME = MENUITEM_VIEW_PERMISSION_NAME
	CHANGE_CHILDREN_PERMISSION_NAME = MENUITEM_CHANGE_CHILDREN_PERMISSION_NAME

	used_permissions = (
		(VIEW_PERMISSION_NAME, _('view')),
		(CHANGE_CHILDREN_PERMISSION_NAME, _('change children')),
	)

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
				return reverse(split[0], args=split[1])
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

	def can_view(self, user):
		permission_name = self.view_permission_name
		return user.has_perm(permission_name, self) or user.has_perm(permission_name)

	def can_view_in_list(self, user):
		return self.can_edit(user) or user.has_perm(self.change_children_permission_name, self)

	def can_edit(self, user):
		permission_name = self.change_children_permission_name
		if user.has_perm(permission_name, self.parent) or user.has_perm(permission_name):
			return True
		if self.parent and self.parent.parent:
			return user.has_perm(permission_name, self.parent.parent)

	def can_delete(self, user):
		return self.can_edit(user)


class AbbreviationExplanation(models.Model):

	abbreviation = models.CharField(max_length=255, unique=True, verbose_name=_("Abbreviation"))
	explanation = models.CharField(max_length=255, blank=False, null=False, verbose_name=_("Explanation"))

	def __str__(self):
		return '*[' + self.abbreviation + ']: ' + self.explanation
