from django.contrib import admin

from guardian.admin import GuardedModelAdmin
from polymorphic.admin import PolymorphicChildModelAdmin

from _1327.documents.models import Document
from _1327.polls.models import Choice, Poll


class ChoiceInline(admin.TabularInline):
	model = Choice
	extra = 3


class PollAdmin(GuardedModelAdmin, PolymorphicChildModelAdmin):
	base_model = Document
	list_display = ('title', 'end_date')
	inlines = [ChoiceInline]


admin.site.register(Poll, PollAdmin)
