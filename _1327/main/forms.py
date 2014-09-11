from django import forms
from django.contrib.auth import authenticate
from django.utils.translation import ugettext_lazy as _

class LoginForm(forms.Form):
	username = forms.CharField(label = _('User name'), max_length = 100)
	password = forms.CharField(label = _('Password'), widget = forms.PasswordInput())

	user_cache = None

	def clean(self):
		cleaned_data = super(LoginForm, self).clean()
		username = cleaned_data.get('username')
		password = cleaned_data.get('password')

		if username and password:
			self.user_cache = authenticate(username=username, password=password)
			if self.user_cache is None:
				self._errors.setdefault('username', forms.util.ErrorList()).append(u"")
				self._errors.setdefault('password', forms.util.ErrorList()).append(u"")
				raise forms.ValidationError(_("Please enter a correct username and password."), 'invalid')
			elif not self.user_cache.is_active:
				raise forms.ValidationError(_("This account is inactive."), 'inactive')
		return cleaned_data

	def get_user(self):
		return self.user_cache