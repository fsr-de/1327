from django.db import models
from django.db.models import Sum

from _1327.user_management.models import UserProfile


QUESTION_VIEW_PERMISSION_NAME = 'view_poll'


class Poll(models.Model):
	title = models.CharField(max_length=255)
	description = models.TextField(default="", blank=True)
	start_date = models.DateField()
	end_date = models.DateField()
	is_multiple_choice_question = models.BooleanField(default=True)
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
		total_votes_for_poll = Choice.objects.filter(poll=self.poll).aggregate(Sum('votes'))['votes__sum']
		return self.votes * 100 / total_votes_for_poll
