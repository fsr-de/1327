from django import forms
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.forms import inlineformset_factory

from _1327.documents.forms import DocumentForm
from _1327.minutes.models import Guest, MinutesDocument
from _1327.minutes.utils import get_last_minutes_document_for_group


class MinutesDocumentForm(DocumentForm):

	class Meta:
		model = MinutesDocument
		fields = ['title', 'date', 'moderator', 'author', 'participants', 'labels', 'state', 'text', 'comment', 'url_title', 'group']

	def __init__(self, *args, **kwargs):
		user = kwargs.pop('user', None)
		creation = kwargs.pop('creation', None)
		creation_group = kwargs.pop('creation_group', None)
		super().__init__(*args, **kwargs)

		if user.is_superuser:
			permitted_groups = Group.objects.filter(permissions__codename="add_minutesdocument")
		else:
			permitted_groups = user.groups.filter(permissions__codename="add_minutesdocument")

		if permitted_groups.count() == 0:  # The user should not be able to view this form
			raise PermissionDenied

		self.fields['group'].queryset = permitted_groups.all()
		self.fields['group'].widget.attrs['class'] = 'select2-selection'
		if creation and creation_group:
			if len(permitted_groups.all()) == 1:
				self.fields['group'].initial = permitted_groups.first()
				self.fields['group'].widget = forms.HiddenInput()
			elif not self.fields['group'].initial:
				self.fields['group'].initial = creation_group

			last_minutes_document = get_last_minutes_document_for_group(creation_group)
			if last_minutes_document:
				self.initial['moderator'] = last_minutes_document.moderator
				self.initial['title'] = last_minutes_document.title
			else:
				self.initial['moderator'] = user
		else:
			self.fields['group'].widget = forms.HiddenInput()
			self.fields['group'].required = False

		if not self.instance.participants.exists() and creation_group:
			self.initial['participants'] = [user.id for user in creation_group.user_set.all()]

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
