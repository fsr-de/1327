from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.core.urlresolvers import NoReverseMatch, reverse
from django.utils.translation import ugettext_lazy as _
from . import models


class MenuItemAdminForm(forms.ModelForm):
	class Meta:
		exclude = []
		model = models.MenuItem

	def clean_link(self):
		data = self.cleaned_data['link']
		if data != "":
			try:
				reverse(data)
			except NoReverseMatch:
				raise ValidationError(_('This link is not valid.'), code='nonexistent')
		return data

	def clean(self):
		if self.cleaned_data['link'] and self.cleaned_data['document']:
			raise ValidationError(_('You are only allowed to define one of Document and Link'))

		return self.cleaned_data


class MenuItemAdmin(admin.ModelAdmin):
	form = MenuItemAdminForm
	list_display = ('title', 'link', 'document')

admin.site.register(models.MenuItem, MenuItemAdmin)
