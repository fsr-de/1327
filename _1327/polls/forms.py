from django import forms

from .models import Poll, Choice


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
