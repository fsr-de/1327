from django.db import models

from _1327.user_management.models import UserProfile


QUESTION_VIEW_PERMISSION_NAME = 'view_poll'


class Poll(models.Model):
	title = models.CharField(max_length=255)
	description = models.TextField(default="", blank=True)
	start_date = models.DateField()
	end_date = models.DateField()
	max_allowed_number_of_answers = models.IntegerField(default=1)
	participants = models.ManyToManyField(UserProfile, related_name="polls", blank=True)

	VIEW_PERMISSION_NAME = QUESTION_VIEW_PERMISSION_NAME

	class Meta:
		permissions = (
			(QUESTION_VIEW_PERMISSION_NAME, 'User/Group is allowed to view that question'),
		)


class Choice(models.Model):
	poll = models.ForeignKey(Poll, related_name="choices")
	text = models.CharField(max_length=255)
	description = models.TextField(default="", blank=True)
	votes = models.IntegerField(default=0)

	def __str__(self):
		return self.text

	def percentage(self):
		participant_count = self.poll.participants.count()
		if participant_count == 0:
			return 0
		return self.votes * 100 / participant_count
