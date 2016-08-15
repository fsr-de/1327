from django import forms
from django.core.exceptions import ValidationError
from django.core.urlresolvers import NoReverseMatch, reverse
from django.db.models import Q
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from guardian.shortcuts import get_objects_for_user, get_perms

from _1327.documents.forms import PermissionBaseForm
from .models import MenuItem


class MenuItemForm(forms.ModelForm):
	class Meta:
		model = MenuItem
		fields = ("title", "document")

	def clean(self):
		if 'link' in self.cleaned_data and self.cleaned_data['link']:
			raise ValidationError(_('You are only allowed to define a document'))
		if 'document' not in self.cleaned_data or self.cleaned_data['document'] is None:
			raise ValidationError(_('You must select a document'))
		return self.cleaned_data


class MenuItemAdminForm(MenuItemForm):
	class Meta:
		model = MenuItem
		fields = ("title", "link", "document")

	def clean_link(self):
		data = self.cleaned_data['link']
		if data != "":
			try:
				reverse(data)
			except NoReverseMatch:
				raise ValidationError(_('This link is not valid.'), code='nonexistent')
		return data

	def clean(self):
		if 'link' in self.cleaned_data and self.cleaned_data['link'] and\
			'document' in self.cleaned_data and self.cleaned_data['document']:
			raise ValidationError(_('You are only allowed to define one of document and link'))
		if ('link' not in self.cleaned_data or self.cleaned_data['link'] == "") and\
			('document' not in self.cleaned_data or self.cleaned_data['document'] is None):
			raise ValidationError(_('You must select a document or link'))
		return self.cleaned_data


class MenuItemCreationForm(MenuItemForm):
	class Meta:
		model = MenuItem
		fields = ("title", "document", "parent")

	def __init__(self, user, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.fields['parent'].required = True
		items_with_perms = get_objects_for_user(user, MenuItem.CHANGE_CHILDREN_PERMISSION_NAME, klass=MenuItem)
		items = []
		for item in items_with_perms:
			items.append(item.pk)
			items.extend([child.pk for child in item.children.all()])

		self.fields['parent'].queryset = MenuItem.objects.filter(Q(pk__in=items) & Q(menu_type=MenuItem.MAIN_MENU) & (Q(parent=None) | Q(parent__parent=None))).order_by('menu_type', 'title')


class MenuItemCreationAdminForm(MenuItemAdminForm):
	class Meta:
		model = MenuItem
		fields = ("title", "link", "document", "parent")

	def __init__(self, user, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.fields['parent'].queryset = MenuItem.objects.filter(Q(menu_type=MenuItem.MAIN_MENU) & (Q(parent=None) | Q(parent__parent=None))).order_by('menu_type', 'title')


class MenuItemPermissionForm(PermissionBaseForm):
	obj = None

	@classmethod
	def header(cls, content_type):
		output = [
			'<tr>',
			'<th class="col-md-6"> {} </th>'.format(_("Role")),
		]
		for permission in sorted(MenuItem.used_permissions):
			item = "<th class=\"col-md-2 text-center\"> {} </th>".format((permission[1]))
			output.append(item)
		output.append('</tr>')
		return mark_safe('\n'.join(output))

	@classmethod
	def prepare_initial_data(cls, groups, content_type, obj=None):
		initial_data = []
		for group in groups:
			if obj is not None:
				group_permissions = get_perms(group, obj)
			else:
				group_permissions = [permission.codename for permission in group.permissions.filter(content_type=content_type)]
			group_permissions = filter(lambda x: any(permission[0] in x for permission in MenuItem.used_permissions), group_permissions)

			data = {permission: True for permission in group_permissions}
			data["group_name"] = group.name
			initial_data.append(data)
		return initial_data


def get_permission_form(menu_item):
	fields = {
		permission[0]: forms.BooleanField(required=False) for permission in MenuItem.used_permissions
	}
	fields['group_name'] = forms.CharField(required=False, widget=forms.HiddenInput())
	return type('PermissionForm', (MenuItemPermissionForm,), {'base_fields': fields, 'obj': menu_item})
