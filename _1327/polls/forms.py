from django import forms
from django.forms import inlineformset_factory
from django.utils.translation import ugettext_lazy as _

from _1327.documents.forms import AtLeastNFormSet, DocumentForm
from .models import Choice, Poll


class PollForm(DocumentForm):
	class Meta:
		model = Poll
		fields = ['title', 'url_title', 'text', 'start_date', 'end_date', 'max_allowed_number_of_answers', 'show_results_immediately', 'comment', ]

	def clean(self):
		super().clean()
		start_date = self.cleaned_data.get('start_date')
		end_date = self.cleaned_data.get('end_date')
		if start_date and end_date:
			if start_date > end_date:
				self.add_error('start_date', forms.ValidationError(_("The start date must be before or on the end date.")))

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
