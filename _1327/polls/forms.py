from django import forms

from _1327.documents.forms import PermissionBaseForm
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
