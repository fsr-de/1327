from datetime import datetime

from django.core.urlresolvers import reverse
from django.db import models
from django.template import Context, loader
from django.utils.translation import ugettext_lazy as _, ungettext_lazy
from reversion import revisions

from _1327.documents.models import Document
from _1327.minutes.fields import HexColorModelField
from _1327.user_management.models import UserProfile

MINUTES_VIEW_PERMISSION_NAME = 'view_minutesdocument'


class MinutesLabel(models.Model):
	title = models.CharField(max_length=255)
	color = HexColorModelField()

	def __str__(self):
		return self.title

	@property
	def class_for_text_color(self):
		# Calculate contrast, see https://24ways.org/2010/calculating-color-contrast/
		r = int(self.color[1:3], 16)
		g = int(self.color[3:5], 16)
		b = int(self.color[5:7], 16)
		yiq = ((r * 299) + (g * 587) + (b * 114)) / 1000
		return 'dark-text' if (yiq >= 128) else 'bright-text'


class MinutesDocument(Document):
	UNPUBLISHED = 0
	PUBLISHED = 1
	INTERNAL = 2
	CHOICES = (
		(UNPUBLISHED, _('Unpublished')),
		(PUBLISHED, _('Published')),
		(INTERNAL, _('Internal')),
	)

	date = models.DateField(default=datetime.now, verbose_name=_("Date"))
	state = models.IntegerField(choices=CHOICES, default=UNPUBLISHED, verbose_name=_("State"))
	moderator = models.ForeignKey(UserProfile, related_name='moderations', verbose_name=_("Moderator"), blank=True, null=True)
	author = models.ForeignKey(UserProfile, related_name='documents')
	participants = models.ManyToManyField(UserProfile, related_name='participations', verbose_name=_("Participants"))
	labels = models.ManyToManyField(MinutesLabel, related_name="minutes", blank=True)

	VIEW_PERMISSION_NAME = MINUTES_VIEW_PERMISSION_NAME

	class Meta(Document.Meta):
		verbose_name = ungettext_lazy("Minutes", "Minutes", 1)
		verbose_name_plural = ungettext_lazy("Minutes", "Minutes", 2)
		permissions = (
			(MINUTES_VIEW_PERMISSION_NAME, 'User/Group is allowed to view those minutes'),
		)

	def get_view_url(self):
		return reverse('documents:view', args=(self.url_title, ))

	def get_edit_url(self):
		return reverse('documents:edit', args=(self.url_title, ))

	def can_be_changed_by(self, user):
		permission_name = 'change_minutesdocument'
		return user.has_perm(permission_name, self) or user.has_perm(permission_name)

	@property
	def meta_information_html(self):
		template = loader.get_template('minutes_meta_information.html')
		return template.render(Context({'document': self}))

revisions.register(MinutesDocument, follow=["document_ptr"])


class Guest(models.Model):
	name = models.CharField(max_length=255, verbose_name=_('Name'))
	minute = models.ForeignKey(MinutesDocument, related_name='guests', verbose_name=_("Guests"))
