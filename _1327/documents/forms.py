from django import forms
from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.core.exceptions import ValidationError
from django.forms import BooleanField
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from guardian.shortcuts import assign_perm, get_perms, remove_perm

from .models import Attachment, Document


class StrippedCharField(forms.CharField):
	"""
		CharField that saves trimmed strings
	"""

	def to_python(self, value):
		super(StrippedCharField, self).to_python(value)
		if value is None:
			return None
		return value.strip()


class DocumentForm(forms.ModelForm):
	url_title = StrippedCharField(label=_('URL'), max_length=255, required=True)
	comment = StrippedCharField(label=_('Comment'), max_length=255, required=True)

	class Meta:
		model = Document
		fields = ['title', 'text', 'comment', 'url_title']

	def clean_url_title(self):
		super().clean()
		url_title = self.cleaned_data['url_title']
		if url_title in settings.FORBIDDEN_URLS:
			raise ValidationError(_('The URL used for this page is not allowed.'))
		if Document.objects.filter(url_title=url_title).exclude(id=self.instance.id).exists():
			raise ValidationError(_('The URL used for this page is already taken.'))
		return url_title

Document.Form = DocumentForm


class PermissionBaseForm(forms.BaseForm):
	"""
		Form that can be used to change permissions of a document object
	"""

	def save(self, model):
		group = Group.objects.get(name=self.cleaned_data["group_name"])
		for field_name, value in self.cleaned_data.items():
			if field_name == 'group_name':
				continue
			if value:
				assign_perm(field_name, group, model)
			else:
				remove_perm(field_name, group, model)

	@classmethod
	def header(cls):
		output = [
			'<tr>',
			'<th class="col-md-6">{}</th>'.format(_("Role")),
		]
		# add one table head entry for every permission in this form
		for permission in sorted([name for name, field in filter(lambda x: type(x[1]) == BooleanField, cls.base_fields.items())]):
			item = "<th class=\"col-md-2 text-center\">{}</th>".format(force_text(_(permission.rsplit('_')[0])))
			output.append(item)
		output.append('</tr>')
		return mark_safe('\n'.join(output))

	def as_table(self):
		"Returns this form rendered as HTML <tr>"
		output = [
			"<tr>",
			"<td>{}</td>".format(force_text(self['group_name'].value()))
		]

		for name in sorted(self.fields.keys()):
			if name == "group_name":
				continue
			output.append('<td class="text-center">{}</td>'.format(force_text(self[name])))
		output.append(force_text(str(self['group_name'])))
		output.append("</tr>")

		return mark_safe('\n'.join(output))

	@classmethod
	def prepare_initial_data(cls, groups, content_type, obj=None):
		initial_data = []
		for group in groups:
			if obj is not None:
				group_permissions = get_perms(group, obj)
			else:
				group_permissions = [permission.codename for permission in group.permissions.filter(content_type=content_type)]

			data = {permission: True for permission in group_permissions}
			data["group_name"] = group.name
			initial_data.append(data)
		return initial_data


def get_permission_form(content_type):
	fields = {
		permission.codename: forms.BooleanField(required=False) for permission in Permission.objects.filter(content_type=content_type)
	}
	fields['group_name'] = forms.CharField(required=False, widget=forms.HiddenInput())
	return type('PermissionForm', (PermissionBaseForm,), {'base_fields': fields})


class AttachmentForm(forms.ModelForm):
	displayname = StrippedCharField(max_length=255, required=False)

	class Meta:
		model = Attachment
		exclude = ('document', 'index')
