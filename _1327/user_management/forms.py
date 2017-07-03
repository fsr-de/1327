from django import forms
from django.utils.translation import ugettext_lazy as _

from _1327.user_management.models import UserProfile


class UserImpersonationForm(forms.Form):
	username = forms.ModelChoiceField(queryset=UserProfile.objects.all(), empty_label=_("Select a user"), required=True)

	def __init__(self, *args, **kwargs):
		super(UserImpersonationForm, self).__init__(*args, **kwargs)
		self.fields['username'].widget.attrs['class'] = 'select2-selection'
