from django.contrib import admin
from guardian.admin import GuardedModelAdmin
from polymorphic.admin import PolymorphicChildModelAdmin

from _1327.documents.models import Document
from _1327.minutes.models import MinutesDocument


class MinutesDocumentAdmin(GuardedModelAdmin, PolymorphicChildModelAdmin):
	base_model = Document
	list_display = ('title', 'author', 'date')

admin.site.register(MinutesDocument, MinutesDocumentAdmin)
