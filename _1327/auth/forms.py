from django import forms
from django.contrib.auth import authenticate
from django.utils.translation import ugettext as _

class LoginForm(forms.Form):
	username = forms.CharField(label = 'User name', max_length = 100)
	password = forms.CharField(label = 'Password', widget = forms.PasswordInput())

	user_cache = None

	def clean_password(self):
		username = self.cleaned_data.get('username')
		password = self.cleaned_data.get('password')

		if username and password:
			self.user_cache = authenticate(username=username, password=password)
			if self.user_cache is None:
				raise forms.ValidationError(_("Please enter a correct username and password."), 'invalid')
			elif not self.user_cache.is_active:
				raise forms.ValidationError(_("This account is inactive."), 'inactive')
		return self.cleaned_data.get('password')

	def get_user(self):
		return self.user_cache
