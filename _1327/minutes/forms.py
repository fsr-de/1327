from django import forms
from django.conf import settings
from django.contrib.auth.models import Group
from django.forms import inlineformset_factory

from _1327.documents.forms import DocumentForm
from _1327.minutes.models import Guest, MinutesDocument


class MinutesDocumentForm(DocumentForm):

	class Meta:
		model = MinutesDocument
		fields = ['title', 'date', 'moderator', 'author', 'participants', 'labels', 'state', 'text', 'comment', 'url_title', 'group']

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		if not self.instance.participants.exists():
			self.initial['participants'] = [user.id for user in Group.objects.get(name=settings.STAFF_GROUP_NAME).user_set.all()]

		self.fields['moderator'].widget.attrs['class'] = 'select2-selection-clearable'
		self.fields['author'].widget.attrs['class'] = 'select2-selection'
		self.fields['participants'].widget.attrs['class'] = 'select2-selection'
		self.fields['labels'].widget.attrs['class'] = 'select2-selection'

	@classmethod
	def get_formset_factory(cls):
		return inlineformset_factory(MinutesDocument, Guest, form=GuestForm, can_delete=True, extra=1)


MinutesDocument.Form = MinutesDocumentForm


class GuestForm(forms.ModelForm):
	class Meta:
		model = Guest
		fields = ['name']


Guest.Form = GuestForm
