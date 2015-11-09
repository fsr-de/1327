from django.conf import settings
from django import forms
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from guardian.shortcuts import get_perms_for_model, assign_perm, remove_perm

from _1327.user_management.models import UserProfile
from _1327.documents.forms import DocumentForm, StrippedCharField
from .models import MinutesDocument


class MinutesDocumentForm(forms.ModelForm):
	url_title = StrippedCharField(label=_('URL'), max_length=255, required=True)
	comment = StrippedCharField(label=_('Comment'), max_length=255, required=True)

	class Meta:
		model = MinutesDocument
		fields = ['title', 'moderator', 'participants', 'text', 'comment', 'url_title']

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		if not self.instance.participants.exists():
			self.initial['participants'] = [user.id for user in Group.objects.get(name=settings.STAFF_GROUP_NAME).user_set.all()]

	def clean_url_title(self):
		super().clean()
		url_title = self.cleaned_data['url_title']
		if MinutesDocument.objects.filter(url_title=url_title).exclude(id=self.instance.id).exists():
			raise ValidationError(_('The URL used for this page is already taken.'))
		return url_title

MinutesDocument.Form = MinutesDocumentForm