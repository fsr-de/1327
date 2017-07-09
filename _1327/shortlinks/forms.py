from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from _1327.main.utils import slugify_and_clean_url_title
from .models import Shortlink


class ShortlinkForm(forms.ModelForm):
	class Meta:
		model = Shortlink
		fields = ("url_title", "link", "document")

	def __init__(self, *args, **kwargs):
		super(ShortlinkForm, self).__init__(*args, **kwargs)
		self.fields['document'].widget.attrs['id'] = 'shortlink-document-selection'

	def clean_url_title(self):
		super().clean()
		url_title = self.cleaned_data['url_title'].lower()
		return slugify_and_clean_url_title(self.instance, url_title)

	def clean(self):
		if 'link' in self.cleaned_data and self.cleaned_data['link'] and\
			'document' in self.cleaned_data and self.cleaned_data['document']:
			raise ValidationError(_('You are only allowed to define one of document and link'))
		if ('link' not in self.cleaned_data or self.cleaned_data['link'] is None) and\
			('document' not in self.cleaned_data or self.cleaned_data['document'] is None):
			raise ValidationError(_('You must select a document or link'))
		return self.cleaned_data
