from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.core.urlresolvers import NoReverseMatch, reverse
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from . import models


class MenuItemAdminForm(forms.ModelForm):
	class Meta:
		exclude = []
		model = models.MenuItem

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		menu_items = models.MenuItem.objects.filter(
			Q(menu_type=models.MenuItem.MAIN_MENU, parent=None) |
			Q(menu_type=models.MenuItem.MAIN_MENU, parent__parent=None)
		)
		self.fields['parent'].queryset = menu_items

	def clean_link(self):
		data = self.cleaned_data['link']
		if data != "":
			try:
				reverse(data)
			except NoReverseMatch:
				raise ValidationError(_('This link is not valid.'), code='nonexistent')
		return data

	def clean(self):
		if 'link' in self.cleaned_data and self.cleaned_data['link'] and\
			'document' in self.cleaned_data and self.cleaned_data['document']:
			raise ValidationError(_('You are only allowed to define one of Document and Link'))
		if self.cleaned_data['menu_type'] == models.MenuItem.FOOTER and self.cleaned_data['parent']:
			raise ValidationError(_('Footer menu items must not have a parent item'))

		return self.cleaned_data


class MenuItemAdmin(admin.ModelAdmin):
	form = MenuItemAdminForm
	list_display = ('title', 'link', 'document')

admin.site.register(models.MenuItem, MenuItemAdmin)
