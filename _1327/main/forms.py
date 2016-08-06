from django import forms
from django.core.exceptions import ValidationError
from django.core.urlresolvers import NoReverseMatch, reverse
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from guardian.shortcuts import get_perms

from _1327.documents.forms import PermissionBaseForm
from .models import MenuItem


class MenuItemForm(forms.ModelForm):
	class Meta:
		model = MenuItem
		fields = ("title", "link", "document")  # TODO (#268): show "link" only for admins

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
			raise ValidationError(_('You are only allowed to define one of Document and Link'))
		if ('link' not in self.cleaned_data or self.cleaned_data['link'] == "") and\
			('document' not in self.cleaned_data or self.cleaned_data['document'] is None):
			raise ValidationError(_('You must select a document or link'))
		return self.cleaned_data


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
