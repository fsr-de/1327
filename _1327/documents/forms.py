from django import forms
from django.utils.translation import ugettext_lazy as _

from .models import Document


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
	type = forms.ChoiceField(choices=Document.types, required=True)
	comment = StrippedCharField(label=_('Comment'), max_length=255, required=True)
