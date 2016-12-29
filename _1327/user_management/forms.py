from django import forms
from django.utils.translation import ugettext_lazy as _

from _1327.user_management.models import UserProfile


class UserImpersonationForm(forms.Form):
	username = forms.ModelChoiceField(queryset=UserProfile.objects.all(), empty_label=_("Select a user"), required=True)
