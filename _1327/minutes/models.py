from django.core.urlresolvers import reverse
from django.db import models
from django.utils.translation import ugettext_lazy as _, ungettext_lazy
from datetime import datetime

import reversion

from _1327.documents.forms import DocumentForm
from _1327.documents.models import Document
from _1327.user_management.models import UserProfile


MINUTES_VIEW_PERMISSION_NAME = 'view_minutesdocument'


class MinutesDocument(Document):
	UNPUBLISHED = 0
	PUBLISHED = 1
	INTERNAL = 2

	date = models.DateField(default=datetime.now, verbose_name=_("Date"))
	state = models.IntegerField(choices=(
		(UNPUBLISHED, _('Unpublished')),
		(PUBLISHED, _('Published')),
		(INTERNAL, _('Internal')),
	), default=UNPUBLISHED, verbose_name=_("State"))
	moderator = models.ForeignKey(UserProfile, related_name='moderations', verbose_name=_("Moderator"))
	author = models.ForeignKey(UserProfile, related_name='documents')
	participants = models.ManyToManyField(UserProfile, related_name='participations', verbose_name=_("Participants"))

	VIEW_PERMISSION_NAME = MINUTES_VIEW_PERMISSION_NAME

	class Meta(Document.Meta):
		verbose_name = ungettext_lazy("Minutes", "Minutes", 1)
		verbose_name_plural = ungettext_lazy("Minutes", "Minutes", 2)
		permissions = (
			(MINUTES_VIEW_PERMISSION_NAME, 'User/Group is allowed to view those minutes'),
		)

	def get_view_url(self):
		return reverse('minutes:view', args=(self.url_title, ))

	def get_edit_url(self):
		return reverse('minutes:edit', args=(self.url_title, ))

	def can_be_changed_by(self, user):
		permission_name = 'change_minutesdocument'
		return user.has_perm(permission_name, self) or user.has_perm(permission_name)

reversion.register(MinutesDocument, follow=["document_ptr"])


class MinutesDocumentForm(DocumentForm):
	class Meta(DocumentForm.Meta):
		model = MinutesDocument

MinutesDocument.Form = MinutesDocumentForm


class MinutesLabel(models.Model):
	title = models.CharField(max_length=255)
	minutes = models.ManyToManyField(MinutesDocument, related_name="labels", blank=True)

	def __str__(self):
		return self.title

