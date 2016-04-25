from django import forms
from django.conf import settings
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory
from django.utils.translation import ugettext_lazy as _

from _1327.documents.forms import DocumentForm
from _1327.minutes.models import Guest, MinutesDocument


class MinutesDocumentForm(DocumentForm):

	class Meta:
		model = MinutesDocument
		fields = ['title', 'date', 'moderator', 'participants', 'labels', 'state', 'text', 'comment', 'url_title', 'groups']

	def __init__(self, *args, **kwargs):
		user = kwargs.pop('user', None)
		super().__init__(*args, **kwargs)
		self.fields["state"].widget = forms.RadioSelect(choices=MinutesDocument.CHOICES)
		staff = Group.objects.get(name=settings.STAFF_GROUP_NAME)
		self.user_groups = user.groups.all()
		self.fields['groups'].queryset = self.user_groups
		self.fields['groups'].min_num = 1
		if staff in self.user_groups:
			self.initial['groups'] = [staff]

		if not self.instance.participants.exists():
			self.initial['participants'] = [user.id for user in Group.objects.get(name=settings.STAFF_GROUP_NAME).user_set.all()]

	def clean_groups(self):
		value = self.cleaned_data['groups']
		if len(value) == 0:
			raise ValidationError(_("You must at least select one group!"))
		for group in value:
			if group not in self.user_groups:
				raise ValidationError(_("You are not a member in this group!"))
		return value

	@classmethod
	def get_formset_factory(cls):
		return inlineformset_factory(MinutesDocument, Guest, form=GuestForm, can_delete=True, extra=1)

MinutesDocument.Form = MinutesDocumentForm


class GuestForm(forms.ModelForm):
	class Meta:
		model = Guest
		fields = ['name']

Guest.Form = GuestForm
