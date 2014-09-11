from django.contrib import admin
from _1327.information_pages.models import Document

class DocumentAdmin(admin.ModelAdmin):
	list_display = ('author', 'title', 'text')
admin.site.register(Document, DocumentAdmin)


