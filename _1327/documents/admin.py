from django.contrib import admin
import reversion

from .models import Document


class DocumentAdmin(reversion.VersionAdmin):
	list_display = ('author', 'title', 'text')
admin.site.register(Document, DocumentAdmin)
