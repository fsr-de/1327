from django.contrib import admin
from guardian.admin import GuardedModelAdmin
from polymorphic.admin import PolymorphicParentModelAdmin
import reversion

from _1327.information_pages.admin import InformationDocumentAdmin
from _1327.information_pages.models import InformationDocument
from .models import Document, Attachment


class DocumentAdmin(GuardedModelAdmin, reversion.VersionAdmin, PolymorphicParentModelAdmin):
	base_model = Document
	child_models = (
		(InformationDocument, InformationDocumentAdmin),
	)

	list_display = ('title', 'author')

admin.site.register(Document, DocumentAdmin)


class AttachmentAdmin(admin.ModelAdmin):
	pass

admin.site.register(Attachment, AttachmentAdmin)
