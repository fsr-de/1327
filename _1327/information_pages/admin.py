from django.contrib import admin
from guardian.admin import GuardedModelAdmin
from polymorphic.admin import PolymorphicChildModelAdmin

from _1327.documents.models import Document
from _1327.information_pages.models import InformationDocument


class InformationDocumentAdmin(GuardedModelAdmin, PolymorphicChildModelAdmin):
	base_model = Document
	list_display = ('title', 'url_title')


admin.site.register(InformationDocument, InformationDocumentAdmin)
