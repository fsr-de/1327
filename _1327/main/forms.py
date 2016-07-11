from django import forms
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.urlresolvers import NoReverseMatch, reverse
from django.utils.translation import ugettext_lazy as _

from _1327.documents.forms import PermissionBaseForm
from _1327.documents.models import Document
from .models import MenuItem


class MenuItemForm(forms.ModelForm):
	class Meta:
		model = MenuItem
		fields = ("title", "link", "document")  # TODO (#268): show "link" only for admins

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.fields['document'].queryset = Document.objects.all().order_by('title')  # TODO (#268): get only items for current user

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


def get_permission_form(menu_item):
	content_type = ContentType.objects.get_for_model(menu_item)
	fields = {
		permission.codename: forms.BooleanField(required=False) for permission in filter(lambda x: 'add' not in x.codename, Permission.objects.filter(content_type=content_type))
	}
	fields['group_name'] = forms.CharField(required=False, widget=forms.HiddenInput())
	return type('PermissionForm', (PermissionBaseForm,), {'base_fields': fields, 'obj': menu_item})
