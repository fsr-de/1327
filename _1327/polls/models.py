from django.db import models
from django.utils.translation import ugettext_lazy as _

from _1327.user_management.models import UserProfile


POLL_VIEW_PERMISSION_NAME = 'view_poll'
POLL_VOTE_PERMISSION_NAME = 'vote_poll'


class Poll(models.Model):
	title = models.CharField(max_length=255)
	description = models.TextField(default="", blank=True)
	start_date = models.DateField()
	end_date = models.DateField()
	max_allowed_number_of_answers = models.IntegerField(default=1)
	participants = models.ManyToManyField(UserProfile, related_name="polls", blank=True)

	VIEW_PERMISSION_NAME = POLL_VIEW_PERMISSION_NAME

	class Meta:
		permissions = (
			(POLL_VIEW_PERMISSION_NAME, 'User/Group is allowed to view that poll'),
			(POLL_VOTE_PERMISSION_NAME, 'User/Group is allowed to participate (vote) in that poll'),
		)


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
