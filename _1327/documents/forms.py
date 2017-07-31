from django import forms
from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.forms import BaseInlineFormSet
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from guardian.shortcuts import assign_perm, get_perms, remove_perm

from _1327.main.utils import slugify_and_clean_url_title
from .models import Attachment, Document


class DocumentForm(forms.ModelForm):
	url_title = forms.CharField(label=_('URL'), max_length=255, required=True)
	comment = forms.CharField(label=_('Comment'), max_length=255, required=False)
	group = forms.ModelChoiceField(Group.objects.all(), label=_('Edit permissions'), disabled=False, required=True)

	class Meta:
		model = Document
		fields = ['title', 'text', 'url_title', 'group', 'comment']

	def __init__(self, *args, **kwargs):
		user = kwargs.pop('user', None)
		creation = kwargs.pop('creation', None)
		kwargs.pop('creation_group', None)
		staff = Group.objects.get(name=settings.STAFF_GROUP_NAME)
		super().__init__(*args, **kwargs)

		add_permission_name = self.Meta.model().add_permission_name.split('.')[1]
		if user.is_superuser:
			permitted_groups = Group.objects.filter(permissions__codename=add_permission_name)
		else:
			permitted_groups = user.groups.filter(permissions__codename=add_permission_name)
			if creation and permitted_groups.count() == 0:  # The user should not be able to view this form
				raise PermissionDenied

		self.fields['group'].queryset = permitted_groups.all()
		self.fields['group'].widget.attrs['class'] = 'select2-selection'
		if creation:
			if len(permitted_groups.all()) == 1:
				self.fields['group'].initial = permitted_groups.first()
				self.fields['group'].widget = forms.HiddenInput()
			elif staff in permitted_groups.all() and not self.fields['group'].initial:
				self.fields['group'].initial = staff
		else:
			self.fields['group'].widget = forms.HiddenInput()
			self.fields['group'].required = False

	def clean_url_title(self):
		super().clean()
		url_title = self.cleaned_data['url_title'].lower()
		return slugify_and_clean_url_title(self.instance, url_title)

	@classmethod
	def get_formset_factory(cls):
		return None


Document.Form = DocumentForm


class PermissionBaseForm(forms.BaseForm):
	"""
		Form that can be used to change permissions
	"""

	obj = None

	def save(self, model):
		group = Group.objects.get(name=self.cleaned_data["group_name"])
		for field_name, value in self.cleaned_data.items():
			if field_name == 'group_name':
				continue
			if value:
				if (group.name == settings.ANONYMOUS_GROUP_NAME or group.name == settings.UNIVERSITY_GROUP_NAME) and field_name != model.view_permission_name:
					continue
				assign_perm(field_name, group, model)
			else:
				remove_perm(field_name, group, model)

	@classmethod
	def header(cls, content_type):
		output = [
			'<tr>',
			'<th class="col-md-6"> {} </th>'.format(_("Role")),
		]
		for permission in sorted(filter(lambda x: 'add' not in x.codename, Permission.objects.filter(content_type=content_type)), key=lambda x: x.codename):
			item = "<th class=\"col-md-2 text-center\"> {} </th>".format(_(permission.codename.rsplit('_')[0]))
			output.append(item)
		output.append('</tr>')
		return mark_safe('\n'.join(output))

	def as_table(self):
		"Returns this form rendered as HTML <tr>"
		output = [
			"<tr>",
			"<td>{}</td>".format(self['group_name'].value())
		]

		for name in sorted(self.fields.keys()):
			if name == "group_name":
				continue
			if (self['group_name'].value() == settings.ANONYMOUS_GROUP_NAME or self['group_name'].value() == settings.UNIVERSITY_GROUP_NAME) and name != self.obj.view_permission_name:
				output.append('<td class="text-center"><input type="checkbox" disabled="disabled" /></td>')
				continue
			output.append('<td class="text-center"> {} </td>'.format(self[name]))
		output.append(str(self['group_name']))
		output.append("</tr>")

		return mark_safe('\n'.join(output))

	def clean(self):
		# make sure that view permission is enabled if other permissions are enabled
		view_permission_enabled = False
		other_permission_enabled = False
		cleaned_data = super(PermissionBaseForm, self).clean()
		for field, __ in filter(lambda x: type(x[1]) == forms.BooleanField, self.fields.items()):
			field_value = cleaned_data.get(field)
			if 'view' in field:
				view_permission_enabled = field_value
			else:
				other_permission_enabled = other_permission_enabled or field_value
		if other_permission_enabled and not view_permission_enabled:
			raise forms.ValidationError(_("If you want to enable additional permissions for a group you also need to enable the view permission for that group!"))

	@classmethod
	def prepare_initial_data(cls, groups, content_type, obj=None):
		initial_data = []
		for group in groups:
			if obj is not None:
				group_permissions = get_perms(group, obj)
			else:
				group_permissions = [permission.codename for permission in group.permissions.filter(content_type=content_type)]
			group_permissions = filter(lambda x: 'add' not in x, group_permissions)
			content_type = ContentType.objects.get_for_model(obj)
			group_permissions = ["{app}.{codename}".format(app=content_type.app_label, codename=codename) for codename in group_permissions]

			data = {permission: True for permission in group_permissions}
			data["group_name"] = group.name
			initial_data.append(data)
		return initial_data


def get_permission_form(document):
	content_type = ContentType.objects.get_for_model(document)
	fields = {
		"{app}.{codename}".format(app=content_type.app_label, codename=permission.codename): forms.BooleanField(required=False)
		for permission in
		filter(lambda x: 'add' not in x.codename, Permission.objects.filter(content_type=content_type))
	}
	fields['group_name'] = forms.CharField(required=False, widget=forms.HiddenInput())
	return type('PermissionForm', (PermissionBaseForm,), {'base_fields': fields, 'obj': document})


class AttachmentForm(forms.ModelForm):
	displayname = forms.CharField(max_length=255, required=False)

	class Meta:
		model = Attachment
		exclude = ('document', 'index', 'hash_value')


class AtLeastNFormSet(BaseInlineFormSet):
	def clean(self):
		super().clean()
		if any(self.errors):
			# There are already errors in the forms contained in this formset
			return
		# check that the minimum required number of forms is met
		count = 0
		for form in self.forms:
			if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
				count += 1

		if count < self.min_num:
			raise forms.ValidationError(_('You must have at least {} of these.'.format(self.min_num)))
