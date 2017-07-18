from django import forms
from django.conf import settings
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.forms import inlineformset_factory

from _1327.documents.forms import DocumentForm
from _1327.minutes.models import Guest, MinutesDocument


class MinutesDocumentForm(DocumentForm):

	class Meta:
		model = MinutesDocument
		fields = ['title', 'date', 'moderator', 'author', 'participants', 'labels', 'state', 'text', 'comment', 'url_title', 'group']

	def __init__(self, *args, **kwargs):
		user = kwargs.pop('user', None)
		creation = kwargs.pop('creation', None)
		super().__init__(*args, **kwargs)
		staff = Group.objects.get(name=settings.STAFF_GROUP_NAME)

		if user.is_superuser:
			permitted_groups = Group.objects.filter(permissions__codename="add_minutesdocument")
		else:
			permitted_groups = user.groups.filter(permissions__codename="add_minutesdocument")

		if permitted_groups.count() == 0:  # The user should not be able to view this form
			raise PermissionDenied

		self.fields['group'].queryset = permitted_groups.all()
		self.fields['group'].widget.attrs['class'] = 'select2-selection'
		if creation:
			if len(permitted_groups.all()) == 1:
				self.fields['group'].initial = permitted_groups.first()
				self.fields['group'].widget = forms.HiddenInput()
			elif staff in permitted_groups.all() and not self.fields['group'].initial:
				self.fields['group'].initial = staff
		else:
			self.fields['group'].widget = forms.HiddenInput()
			self.fields['group'].required = False

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
