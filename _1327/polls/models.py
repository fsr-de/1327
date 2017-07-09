from datetime import date, datetime

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Sum
from django.template import loader
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from guardian.shortcuts import assign_perm

from reversion import revisions

from _1327.documents.markdown_internal_link_pattern import InternalLinkPattern
from _1327.documents.models import Document
from _1327.user_management.models import UserProfile


POLL_VIEW_PERMISSION_NAME = 'view_poll'
POLL_VOTE_PERMISSION_NAME = 'vote_poll'


class Poll(Document):

	def can_be_changed_by(self, user):
		permission_name = self.edit_permission_name
		return user.has_perm(permission_name, self) or user.has_perm(permission_name)

	@property
	def can_be_reverted(self):
		return self.participants.count() == 0

	start_date = models.DateField(default=datetime.now, verbose_name=_("Start Date"))
	end_date = models.DateField(default=datetime.now, verbose_name=_("End Date"))
	max_allowed_number_of_answers = models.PositiveIntegerField(default=1)
	participants = models.ManyToManyField(UserProfile, related_name="polls", blank=True)
	show_results_immediately = models.BooleanField(default=True, verbose_name=_("show results immediately after vote"))

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
				return reverse(poll.get_view_url_name(), args=[poll.id])
			return ''

	@classmethod
	def generate_new_title(cls):
		return _("New Poll")

	@classmethod
	def get_vote_permission(klass):
		content_type = ContentType.objects.get_for_model(klass)
		app_label = content_type.app_label
		permission = "{app}.{permission_name}".format(app=app_label, permission_name=klass.VOTE_PERMISSION_NAME)
		return permission

	@classmethod
	def generate_default_slug(cls, title):
		slug_final = slug = "new-poll-from-{}".format(date.today().isoformat())
		count = 2
		while Poll.objects.filter(url_title=slug_final).exists():
			slug_final = "{}_{}".format(slug, count)
			count += 1
		return slug_final

	@property
	def vote_permission_name(self):
		return Poll.get_vote_permission()

	def get_view_url(self):
		return reverse(self.get_view_url_name(), args=(self.url_title,))

	def get_edit_url(self):
		return reverse(self.get_edit_url_name(), args=(self.url_title,))

	def get_view_url_name(self):
		return 'polls:view'

	def get_edit_url_name(self):
		return 'polls:edit'

	def get_attachments_url_name(self):
		return 'polls:attachments'

	def get_permissions_url_name(self):
		return 'polls:permissions'

	def get_versions_url_name(self):
		return 'polls:versions'

	def get_publish_url_name(self):
		return 'documents:publish'

	def save_formset(self, formset):
		choices = formset.save(commit=False)
		for choice in formset.deleted_objects:
			choice.delete()
		for choice in choices:
			choice.poll = self
			choice.save()

	@property
	def num_votes(self):
		return self.choices.aggregate(Sum('votes')).get('votes__sum')

	@property
	def meta_information_html(self):
		return loader.get_template('polls_meta_information.html')

	def handle_edit(self, cleaned_data):
		content_type = ContentType.objects.get_for_model(self)
		groups = cleaned_data['vote_groups']
		for group in groups:
			assign_perm("{app}.view_{model}".format(app=content_type.app_label, model=content_type.model), group, self)
			assign_perm("{app}.vote_{model}".format(app=content_type.app_label, model=content_type.model), group, self)

	@property
	def has_choice_descriptions(self):
		for choice in self.choices.all():
			if choice.description:
				return True
		return False


revisions.register(Poll, follow=["document_ptr"])


class Choice(models.Model):
	poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name="choices")
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
