from datetime import datetime

from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Sum
from django.template import Context, loader
from django.utils.translation import ugettext_lazy as _

from reversion import revisions

from _1327.documents.markdown_internal_link_pattern import InternalLinkPattern
from _1327.documents.models import Document
from _1327.user_management.models import UserProfile


POLL_VIEW_PERMISSION_NAME = 'view_poll'
POLL_VOTE_PERMISSION_NAME = 'vote_poll'


class Poll(Document):

	def can_be_changed_by(self, user):
		permission_name = 'change_poll'
		return user.has_perm(permission_name, self) or user.has_perm(permission_name)

	start_date = models.DateField(default=datetime.now, verbose_name=_("Start Date"))
	end_date = models.DateField(default=datetime.now, verbose_name=_("End Date"))
	max_allowed_number_of_answers = models.IntegerField(default=1)
	participants = models.ManyToManyField(UserProfile, related_name="polls", blank=True)

	VIEW_PERMISSION_NAME = POLL_VIEW_PERMISSION_NAME
	VOTE_PERMISSION_NAME = POLL_VOTE_PERMISSION_NAME
	POLLS_LINK_REGEX = r'\[(?P<title>[^\[]+)\]\(poll:(?P<id>\d+)\)'

	class Meta:
		permissions = (
			(POLL_VIEW_PERMISSION_NAME, 'User/Group is allowed to view that poll'),
			(POLL_VOTE_PERMISSION_NAME, 'User/Group is allowed to participate (vote) in that poll'),
		)

	class LinkPattern (InternalLinkPattern):

		def url(self, id):
			poll = Poll.objects.get(id=id)
			if poll:
				return reverse('documents:view', args=[poll.id])
			return ''

	def get_view_url(self):
		return reverse('documents:view', args=(self.url_title,))

	def get_edit_url(self):
		return reverse('documents:edit', args=(self.url_title,))

	def save_formset(self, formset):
		choices = formset.save(commit=False)
		for choice in formset.deleted_objects:
			choice.delete()
		for choice in choices:
			choice.poll = self
			choice.save()

	@property
	def votes(self):
		return self.choices.all().aggregate(Sum('votes')).popitem()[1]

	@property
	def meta_information_html(self):
		template = loader.get_template('polls_meta_information.html')
		return template.render(Context({'document': self}))

revisions.register(Poll, follow=["document_ptr"])


class Choice(models.Model):
	poll = models.ForeignKey(Poll, related_name="choices")
	text = models.CharField(max_length=255)
	description = models.TextField(default="", blank=True)
	votes = models.IntegerField(default=0)

	index = models.IntegerField(verbose_name=_("ordering index"), default=0)

	class Meta:
		ordering = ['index']

	def __str__(self):
		return self.text

	def percentage(self):
		participant_count = self.poll.participants.count()
		if participant_count == 0:
			return 0
		return self.votes * 100 / participant_count
