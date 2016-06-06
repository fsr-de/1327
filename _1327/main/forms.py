from django import forms
from django.core.exceptions import ValidationError
from django.core.urlresolvers import NoReverseMatch, reverse
from django.utils.translation import ugettext_lazy as _

from _1327.documents.models import Document
from .models import MenuItem


class MenuItemForm(forms.ModelForm):
	class Meta:
		model = MenuItem
		fields = ("title", "link", "document", "staff_only")  # TODO (#268): show "display for staff only" and "link" only for admins

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
