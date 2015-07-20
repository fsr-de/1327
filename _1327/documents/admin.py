from django.contrib import admin
from guardian.admin import GuardedModelAdmin
from polymorphic.admin import PolymorphicParentModelAdmin
import reversion

from _1327.information_pages.admin import InformationDocumentAdmin
from _1327.information_pages.models import InformationDocument
from _1327.minutes.admin import MinutesDocumentAdmin
from _1327.minutes.models import MinutesDocument

from .models import Document, Attachment


class DocumentAdmin(GuardedModelAdmin, reversion.VersionAdmin, PolymorphicParentModelAdmin):
	base_model = Document
	child_models = (
		(InformationDocument, InformationDocumentAdmin),
		(MinutesDocument, MinutesDocumentAdmin),
	)

	list_display = ('title', 'url_title')

admin.site.register(Document, DocumentAdmin)


class AttachmentAdmin(admin.ModelAdmin):
	pass

admin.site.register(Attachment, AttachmentAdmin)
