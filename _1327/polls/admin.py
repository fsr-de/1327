from django.contrib import admin

from _1327.polls.models import Choice, Poll


class ChoiceInline(admin.TabularInline):
	model = Choice
	extra = 3


class QuestionAdmin(admin.ModelAdmin):
	list_display = ('title', 'end_date')
	inlines = [ChoiceInline]


admin.site.register(Poll, QuestionAdmin)
