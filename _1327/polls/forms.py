from django import forms

from .models import Choice, Poll


class PollForm(forms.ModelForm):
	class Meta:
		model = Poll
		exclude = ["participants"]


class ChoiceForm(forms.ModelForm):
	class Meta:
		model = Choice
		exclude = ["poll", "votes"]
		widgets = {
			"description": forms.TextInput(),
			"index": forms.HiddenInput()
		}
