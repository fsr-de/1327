from django.contrib import admin
from guardian.admin import GuardedModelAdmin
from polymorphic.admin import PolymorphicParentModelAdmin
from reversion.admin import VersionAdmin

from _1327.information_pages.models import InformationDocument
from _1327.minutes.models import MinutesDocument

from .models import Attachment, Document


class DocumentAdmin(GuardedModelAdmin, VersionAdmin, PolymorphicParentModelAdmin):
	base_model = Document
	child_models = (InformationDocument, MinutesDocument)
	list_display = ('title', 'url_title')


admin.site.register(Document, DocumentAdmin)


class AttachmentAdmin(admin.ModelAdmin):
	pass


admin.site.register(Attachment, AttachmentAdmin)
