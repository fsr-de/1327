from django import forms
from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.urls import NoReverseMatch, reverse
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from guardian.shortcuts import get_objects_for_user, get_perms

from _1327.documents.forms import PermissionBaseForm
from _1327.main.models import AbbreviationExplanation
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
		if data is not None:
			try:
				split = data.split("?")
				if len(split) == 1:
					reverse(split[0])
				elif len(split) == 2:
					arguments = split[1].split('=')
					if len(arguments) == 1:
						raise ValidationError(_('Arguments for links must be provided as keyword arguments.'))
					reverse(split[0], kwargs={arguments[0]: arguments[1]})
				else:
					raise ValidationError(_('This link is not valid.'), code='nonexistent')
			except NoReverseMatch:
				raise ValidationError(_('This link is not valid.'), code='nonexistent')
		return data

	def clean(self):
		if 'link' in self.cleaned_data and self.cleaned_data['link'] and\
			'document' in self.cleaned_data and self.cleaned_data['document']:
			raise ValidationError(_('You are only allowed to define one of document and link'))
		if ('link' not in self.cleaned_data or self.cleaned_data['link'] is None) and\
			('document' not in self.cleaned_data or self.cleaned_data['document'] is None):
			raise ValidationError(_('You must select a document or link'))
		return self.cleaned_data


class MenuItemCreationForm(MenuItemForm):
	group = forms.ModelChoiceField(Group.objects.all(), label=_('Edit permissions'), disabled=False, required=True)

	class Meta:
		model = MenuItem
		fields = ("title", "document", "parent", "group")

	def __init__(self, user, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.user_groups = user.groups.all()
		self.fields['parent'].required = True
		items_with_perms = get_objects_for_user(user, MenuItem.CHANGE_CHILDREN_PERMISSION_NAME, klass=MenuItem)
		items = []
		for item in items_with_perms:
			items.append(item.pk)
			items.extend([child.pk for child in item.children.all()])
		staff = Group.objects.get(name=settings.STAFF_GROUP_NAME)
		self.fields['group'].queryset = self.user_groups
		if staff in self.user_groups and not self.fields['group'].initial:
			self.fields['group'].initial = staff
		elif len(self.user_groups) == 1:
			self.fields['group'].initial = self.user_groups[0]
			self.fields['group'].widget = forms.HiddenInput()

		self.fields['parent'].queryset = MenuItem.objects.filter(Q(pk__in=items) & Q(menu_type=MenuItem.MAIN_MENU) & (Q(parent=None) | Q(parent__parent=None))).order_by('menu_type', 'title')

	def clean_group(self):
		value = self.cleaned_data['group']
		if value and value not in self.user_groups:
			raise ValidationError(_("You are not a member of this group!"))
		return value


class MenuItemCreationAdminForm(MenuItemAdminForm):
	group = forms.ModelChoiceField(Group.objects.all(), label=_('Edit permissions'), disabled=False, required=True)

	class Meta:
		model = MenuItem
		fields = ("title", "link", "document", "parent", "group")

	def __init__(self, user, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.user_groups = user.groups.all()
		self.fields['parent'].queryset = MenuItem.objects.filter(Q(menu_type=MenuItem.MAIN_MENU) & (Q(parent=None) | Q(parent__parent=None))).order_by('menu_type', 'title')
		staff = Group.objects.get(name=settings.STAFF_GROUP_NAME)
		self.fields['group'].queryset = self.user_groups
		if staff in self.user_groups and not self.fields['group'].initial:
			self.fields['group'].initial = staff
		elif len(self.user_groups) == 1:
			self.fields['group'].initial = self.user_groups[0]
			self.fields['group'].widget = forms.HiddenInput()

	def clean_group(self):
		value = self.cleaned_data['group']
		if value and value not in self.user_groups:
			raise ValidationError(_("You are not a member of this group!"))
		return value


class MenuItemPermissionForm(PermissionBaseForm):
	obj = None

	@classmethod
	def header(cls, content_type):
		output = [
			'<tr>',
			'<th class="col-md-6"> {} </th>'.format(_("Role")),
		]
		for permission in sorted(MenuItem.used_permissions()):
			item = "<th class=\"col-md-2 text-center\"> {} </th>".format(permission.description)
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
			content_type = ContentType.objects.get_for_model(obj)
			group_permissions = ["{app}.{codename}".format(app=content_type.app_label, codename=codename) for codename in group_permissions]
			group_permissions = filter(lambda x: any(permission.name in x for permission in MenuItem.used_permissions()), group_permissions)

			data = {permission: True for permission in group_permissions}
			data["group_name"] = group.name
			initial_data.append(data)
		return initial_data


class AbbreviationExplanationForm(forms.ModelForm):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.fields["abbreviation"].widget = forms.TextInput(attrs={'class': 'form-control'})
		self.fields["explanation"].widget = forms.TextInput(attrs={'class': 'form-control'})

	class Meta:
		model = AbbreviationExplanation
		fields = "__all__"


def get_permission_form(menu_item):
	fields = {
		permission.name: forms.BooleanField(required=False) for permission in MenuItem.used_permissions()
	}
	fields['group_name'] = forms.CharField(required=False, widget=forms.HiddenInput())
	return type('PermissionForm', (MenuItemPermissionForm,), {'base_fields': fields, 'obj': menu_item})
