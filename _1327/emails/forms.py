from django import forms


class QuickSearchForm(forms.Form):
	text = forms.CharField(label='Fulltext search', required=True)


class SearchForm(forms.Form):
	text = forms.CharField(label='Fulltext search', required=False)
	sender = forms.CharField(label='From address', required=False)
	receiver = forms.CharField(label='To / CC address', required=False)
	received_before = forms.DateField(required=False)
	received_after = forms.DateField(required=False)
	has_attachments = forms.BooleanField(required=False)

	def clean(self):
		if len(self.cleaned_data['text']) == 0 and len(self.cleaned_data['sender']) == 0 and \
			len(self.cleaned_data['receiver']) == 0 and not self.cleaned_data['received_before'] \
			and not self.cleaned_data['received_after'] and not self.cleaned_data['has_attachments']:
			raise forms.ValidationError("You need to narrow down your search.")

		return self.cleaned_data
