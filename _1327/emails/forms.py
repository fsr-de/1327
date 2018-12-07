from django import forms
from django.utils.translation import gettext_lazy as _


class QuickSearchForm(forms.Form):
	text = forms.CharField(label=_('Fulltext search'), required=True)


class SearchForm(forms.Form):
	text = forms.CharField(label=_('Fulltext search'), required=False)
	sender = forms.CharField(label=_('From address'), required=False)
	receiver = forms.CharField(label=_('To / CC address'), required=False)
	received_before = forms.DateField(label=_('Received before'), required=False)
	received_after = forms.DateField(label=_('Received after'), required=False)
	has_attachments = forms.BooleanField(label=_('Has attachments'), required=False)

	def clean(self):
		if len(self.cleaned_data['text']) == 0 and len(self.cleaned_data['sender']) == 0 and \
			len(self.cleaned_data['receiver']) == 0 and not self.cleaned_data['received_before'] \
			and not self.cleaned_data['received_after'] and not self.cleaned_data['has_attachments']:
			raise forms.ValidationError("You need to narrow down your search.")

		return self.cleaned_data
