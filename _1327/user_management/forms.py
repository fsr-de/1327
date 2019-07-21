from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.models import Group
from django.forms import BooleanField, ModelMultipleChoiceField
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.debug import sensitive_variables

from _1327.user_management.models import UserProfile


class LoginUsernameForm(forms.Form):
	"""
		Form encapsulating the login with username and password, for example from an Active Directory.
	"""
	username = forms.CharField(label=_("Username"), max_length=254)
	password = forms.CharField(label=_("Password"), widget=forms.PasswordInput)

	def __init__(self, request=None, *args, **kwargs):
		self.request = request
		self.user_cache = None
		super().__init__(*args, **kwargs)

	@sensitive_variables('password')
	def clean_password(self):
		username = self.cleaned_data.get('username')
		password = self.cleaned_data.get('password')

		# django-auth-kerberos might create a new userprofile. make sure it gets a lowercase username.
		username = username.lower()

		if username and password:
			self.user_cache = authenticate(username=username, password=password)
			if self.user_cache is None:
				raise forms.ValidationError(_("Please enter a correct username and password."))
		return password

	def get_user_id(self):
		if self.user_cache:
			return self.user_cache.id
		return None

	def get_user(self):
		return self.user_cache


class UserImpersonationForm(forms.Form):
	username = forms.ModelChoiceField(queryset=UserProfile.objects.all(), empty_label=_("Select a user"), required=True)

	def __init__(self, *args, **kwargs):
		super(UserImpersonationForm, self).__init__(*args, **kwargs)
		self.fields['username'].widget.attrs['class'] = 'select2-selection'


class GroupEdit(forms.ModelForm):
	add_information_document = BooleanField(required=False)
	add_minutes = BooleanField(required=False)
	add_poll = BooleanField(required=False)
	users = ModelMultipleChoiceField(UserProfile.objects.all())

	class Meta:
		model = Group
		fields = ("name",)

	def __init__(self, *args, **kwargs):
		super().__init__(**kwargs)
		self.fields['users'].widget.attrs['class'] = 'select2-selection'

	def save(self, *args, **kwargs):
		super().save(*args, **kwargs)
		instance = forms.ModelForm.save(self)
		instance.user_set.clear()
		instance.user_set.add(*self.cleaned_data["users"])
		return instance
