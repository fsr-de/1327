from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from _1327.tenca_django.models import HashEntry, LegacyAdminURL


@admin.register(HashEntry)
class HashEntryAdmin(admin.ModelAdmin):
	list_display = ('list_id', 'hash_id', 'link_legacy_admin_url', 'link_manage_page')
	search_fields = ('list_id', )

	def _link(self, text, url):
		return format_html('<a href="{}">{}</a>'.format(url, text))

	def link_legacy_admin_url(self, obj):
		try:
			legacy_link = LegacyAdminURL.objects.get(hash_id_id=obj.id)
			text = _('Edit')
			url = reverse('admin:tenca_django_legacyadminurl_change', args=(legacy_link.id, ))
		except LegacyAdminURL.DoesNotExist:
			text = _('Add')
			url = reverse('admin:tenca_django_legacyadminurl_add')
		return self._link(text, url)

	link_legacy_admin_url.short_description = 'Legacy Admin URL'

	def link_manage_page(self, obj):
		return self._link(
			_('Manage List'),
			reverse('tenca_django:tenca_manage_list', args=(obj.list_id, ))
		)

	link_manage_page.short_description = 'Management Page'


@admin.register(LegacyAdminURL)
class LegacyAdminURLAdmin(admin.ModelAdmin):
	list_display = ('view_list_id', 'admin_url')

	def view_list_id(self, obj):
		return obj.hash_id.list_id

	view_list_id.short_description = 'List id'
