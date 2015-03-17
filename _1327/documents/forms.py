from django import forms
from django.contrib.auth.models import Group
from django.utils.translation import ugettext_lazy as _
from guardian.shortcuts import get_perms_for_model, assign_perm, remove_perm


class StrippedCharField(forms.CharField):
	"""
		CharField that does not allow to save string that only contain whitespaces
	"""

	def to_python(self, value):
		super(StrippedCharField, self).to_python(value)
		return value.strip()


class TextForm(forms.Form):

	title = StrippedCharField(label=_('Title'), max_length=255, required=True)
	text = StrippedCharField(label=_('Text'), required=True)
	comment = StrippedCharField(label=_('Comment'), max_length=255, required=True)


class PermissionForm(forms.Form):
	"""
		Form that can be used to change permissions of a document object
	"""

	change_permission = forms.BooleanField(required=False)
	delete_permission = forms.BooleanField(required=False)
	view_permission = forms.BooleanField(required=False)
	group_name = forms.CharField(required=False)


	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.fields["group_name"].widget = forms.HiddenInput()

	def save(self, model):
		group = Group.objects.get(name=self.cleaned_data["group_name"])
		possible_permissions = get_perms_for_model(model)
		for permission in possible_permissions:
			if "change" in str(permission):
				if self.cleaned_data["change_permission"]:
					assign_perm(permission.codename, group, model)
				else:
					remove_perm(permission.codename, group, model)
			elif "delete" in str(permission):
				if self.cleaned_data["delete_permission"]:
					assign_perm(permission.codename, group, model)
				else:
					remove_perm(permission.codename, group, model)
			elif "view" in str(permission):
				if self.cleaned_data["view_permission"]:
					assign_perm(permission.codename, group, model)
				else:
					remove_perm(permission.codename, group, model)
