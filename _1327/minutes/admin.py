from django import forms
from django.contrib import admin

from guardian.admin import GuardedModelAdmin
from polymorphic.admin import PolymorphicChildModelAdmin

from _1327.documents.models import Document
from _1327.minutes.models import HexColorModelField, MinutesDocument, MinutesLabel


class MinutesDocumentAdmin(GuardedModelAdmin, PolymorphicChildModelAdmin):
	base_model = Document
	list_display = ('title', 'author', 'date')


class MinutesLabelAdmin(admin.ModelAdmin):
	base_model = MinutesLabel
	list_display = ('title', 'color', )
	fields = ('title', 'color', )
	formfield_overrides = {
		HexColorModelField: {'widget': forms.TextInput(attrs={'placeholder': '#000000', 'class': 'vTextField'})}
	}


admin.site.register(MinutesDocument, MinutesDocumentAdmin)
admin.site.register(MinutesLabel, MinutesLabelAdmin)
