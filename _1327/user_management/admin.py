import csv
from io import StringIO
import re

from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render
from django.urls import path
from django.utils.translation import gettext_lazy as _

from .forms import GroupEditForm
from .models import UserProfile


class UserCreationForm(forms.ModelForm):
	"""A form for creating new users. Includes all the required fields, plus a repeated password."""
	password1 = forms.CharField(label=_('Password'), widget=forms.PasswordInput)
	password2 = forms.CharField(label=_('Password confirmation'), widget=forms.PasswordInput)

	class Meta:
		model = UserProfile
		fields = ('username', 'email', 'first_name', 'last_name')

	def clean_password2(self):
		# Check that the two password entries match
		password1 = self.cleaned_data.get("password1")
		password2 = self.cleaned_data.get("password2")
		if password1 and password2 and password1 != password2:
			raise forms.ValidationError(_("Passwords don't match"))
		return password2

	def save(self, commit=True):
		# Save the provided password in hashed format
		user = super(UserCreationForm, self).save(commit=False)
		user.set_password(self.cleaned_data["password1"])
		if commit:
			user.save()
		return user


class UserChangeForm(forms.ModelForm):
	"""A form for updating users. Includes all the fields on the user, but replaces the password field with admin's password hash display field."""
	password = ReadOnlyPasswordHashField()

	class Meta:
		model = UserProfile
		fields = ('username', 'password', 'email', 'first_name', 'last_name', 'is_active')

	def clean_password(self):
		# Regardless of what the user provides, return the initial value.
		# This is done here, rather than on the field, because the
		# field does not have access to the initial value
		return self.initial["password"]


class UserProfileAdmin(UserAdmin):
	# The forms to add and change user instances
	form = UserChangeForm
	add_form = UserCreationForm

	# The fields to be used in displaying the User model.
	# These override the definitions on the base UserAdmin
	# that reference specific fields on auth.User.
	list_display = ('username', 'email', 'first_name', 'last_name', 'is_superuser')
	list_filter = ('is_superuser',)
	fieldsets = (
		(None, {'fields': ('username', 'email', 'password')}),
		('Personal info', {'fields': ('first_name', 'last_name')}),
		('Permissions', {'fields': ('is_superuser', 'groups', 'user_permissions')}),
	)
	# add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
	# overrides get_fieldsets to use this attribute when creating a user.
	add_fieldsets = (
		(
			None, {
				'classes': ('wide',),
				'fields': ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
			}
		),
	)
	search_fields = ('username',)
	ordering = ('username',)

	change_list_template = "entities/user_change_list.html"

	def get_urls(self):
		urls = super().get_urls()
		my_urls = [
			path('import-csv/', self.import_csv),
		]
		return my_urls + urls

	def import_csv(self, request):
		if request.method == "POST":
			csv_file = request.FILES["csv_file"]
			csv_input = csv_file.read().decode('utf-8')
			reader = csv.reader(StringIO(csv_input), delimiter=',')

			internal_domains = list(map(lambda email_replacement: email_replacement[1], settings.INSTITUTION_EMAIL_REPLACEMENTS))

			for row in reader:
				email = row[1]
				if re.match(r'.*@.*', email) is None:
					raise ValidationError(f'Error parsing email "{email}"')
				prefix = email.split('@')[0]

				user = UserProfile.objects.filter(email__startswith=prefix + "@").first()
				if user.email != email:
					old_domain = user.email.split('@')[1]
					new_domain = email.split('@')[1]

					if old_domain in internal_domains and new_domain in internal_domains:
						user.email = email
						user.save()
			self.message_user(request, "Your csv file has been imported")
			return redirect("..")
		form = CsvImportForm()
		payload = {"form": form}
		return render(
			request, "admin/csv_form.html", payload
		)


# Now register the new UserAdmin...
admin.site.register(UserProfile, UserProfileAdmin)


class CsvImportForm(forms.Form):
	csv_file = forms.FileField()


class GroupAdminForm(forms.ModelForm):
	"""
		Adapted Group Admin Form that allows to select users belonging to each group and also mimics that standard
		permissions are only default permissions
		based on: https://djangosnippets.org/snippets/2452/

	"""
	users = forms.ModelMultipleChoiceField(
		queryset=UserProfile.objects.all(),
		widget=FilteredSelectMultiple(_('Users'), False),
		required=False
	)

	class Meta:
		exclude = []
		model = Group

	def __init__(self, *args, **kwargs):
		instance = kwargs.get('instance', None)
		if instance is not None:
			initial = kwargs.get('initial', {})
			initial['users'] = instance.user_set.all()
			initial['default_permissions'] = instance.permissions.all()
			kwargs['initial'] = initial
		super(GroupAdminForm, self).__init__(*args, **kwargs)

	def save(self, commit=True):
		group = super(GroupAdminForm, self).save(commit=commit)

		if commit:
			group.user_set.set(self.cleaned_data['users'])
		else:
			old_save_m2m = self.save_m2m

			def new_save_m2m():
				old_save_m2m()
				group.user_set.set(self.cleaned_data['users'])

			self.save_m2m = new_save_m2m
		return group


class MyGroupAdmin(GroupAdmin):
	form = GroupEditForm


admin.site.unregister(Group)
admin.site.register(Group, MyGroupAdmin)
