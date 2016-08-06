from django import forms
from django.forms import inlineformset_factory

from _1327.documents.forms import AtLeastNFormSet, DocumentForm
from .models import Choice, Poll


class PollForm(DocumentForm):
	class Meta:
		model = Poll
		fields = ['title', 'url_title', 'text', 'start_date', 'end_date', 'max_allowed_number_of_answers', 'comment', ]

	@classmethod
	def get_formset_factory(cls):
		return inlineformset_factory(
			Poll,
			Choice,
			form=ChoiceForm,
			extra=1,
			can_delete=True,
			min_num=2,
			validate_min=True,
			formset=AtLeastNFormSet,
		)

Poll.Form = PollForm


class ChoiceForm(forms.ModelForm):
	class Meta:
		model = Choice
		exclude = ["poll", "votes"]
		widgets = {
			"description": forms.TextInput(),
			"index": forms.HiddenInput(),
		}
