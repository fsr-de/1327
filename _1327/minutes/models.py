from datetime import date, datetime

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.exceptions import SuspiciousOperation
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template import loader
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _, ungettext_lazy
from guardian.shortcuts import assign_perm
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
	CUSTOM = 3
	PUBLISHED_STUDENT = 4
	CHOICES = (
		(UNPUBLISHED, _('Unpublished')),
		(PUBLISHED, _('Published for Students and University Network')),
		(INTERNAL, _('Internal')),
		(CUSTOM, _('Custom')),
		(PUBLISHED_STUDENT, _('Published for Students only')),
	)

	date = models.DateField(default=datetime.now, verbose_name=_("Date"))
	state = models.IntegerField(choices=CHOICES, default=UNPUBLISHED, verbose_name=_("State"))
	moderator = models.ForeignKey(UserProfile, on_delete=models.PROTECT, related_name='moderations', verbose_name=_("Moderator"), blank=True, null=True)
	author = models.ForeignKey(UserProfile, on_delete=models.PROTECT, related_name='documents')
	participants = models.ManyToManyField(UserProfile, related_name='participations', verbose_name=_("Participants"))
	labels = models.ManyToManyField(MinutesLabel, related_name="minutes", blank=True)

	VIEW_PERMISSION_NAME = MINUTES_VIEW_PERMISSION_NAME

	class Meta(Document.Meta):
		verbose_name = ungettext_lazy("Minutes", "Minutes", 1)
		verbose_name_plural = ungettext_lazy("Minutes", "Minutes", 2)
		permissions = (
			(MINUTES_VIEW_PERMISSION_NAME, 'User/Group is allowed to view those minutes'),
		)

	@classmethod
	def generate_new_title(cls):
		return _("Minutes")

	@classmethod
	def generate_default_slug(cls, title):
		slug_final = slug = date.today().isoformat()
		count = 2
		while MinutesDocument.objects.filter(url_title=slug_final).exists():
			slug_final = "{}_{}".format(slug, count)
			count += 1
		return slug_final

	def get_view_url(self):
		return reverse(self.get_view_url_name(), args=(self.url_title, ))

	def get_edit_url(self):
		return reverse(self.get_edit_url_name(), args=(self.url_title, ))

	def get_view_url_name(self):
		return 'minutes:view'

	def get_edit_url_name(self):
		return 'minutes:edit'

	def get_attachments_url_name(self):
		return 'minutes:attachments'

	def get_permissions_url_name(self):
		return 'minutes:permissions'

	def get_versions_url_name(self):
		return 'minutes:versions'

	def get_publish_url_name(self):
		return 'documents:publish'

	def can_be_changed_by(self, user):
		permission_name = self.edit_permission_name
		return user.has_perm(permission_name, self) or user.has_perm(permission_name)

	def show_permissions_editor(self):
		return self.state == MinutesDocument.CUSTOM

	def show_publish_button(self):
		return not self.is_in_creation and self.state == MinutesDocument.UNPUBLISHED

	def publish(self, state_id):
		if state_id not in (MinutesDocument.PUBLISHED, MinutesDocument.PUBLISHED_STUDENT):
			self.state = int(state_id)
			self.save()
		else:
			raise SuspiciousOperation

	@property
	def meta_information_html(self):
		return loader.get_template('minutes_meta_information.html')

	def save_formset(self, formset):
		guests = formset.save(commit=False)
		for guest in formset.deleted_objects:
			guest.delete()
		for guest in guests:
			guest.minute = self
			guest.save()

	def handle_edit(self, cleaned_data):
		self.participants.clear()
		for participant in cleaned_data['participants']:
			self.participants.add(participant)
		self.labels.clear()
		for label in cleaned_data['labels']:
			self.labels.add(label)


revisions.register(MinutesDocument, follow=["document_ptr"])


@receiver(post_save, sender=MinutesDocument, dispatch_uid="update_permissions")
def update_permissions(sender, instance, **kwargs):
	student_group = Group.objects.get(name=settings.STUDENT_GROUP_NAME)
	university_network_group = Group.objects.get(name=settings.UNIVERSITY_GROUP_NAME)
	if instance.state == MinutesDocument.UNPUBLISHED or instance.state == MinutesDocument.INTERNAL:
		instance.delete_all_permissions(student_group)
		instance.delete_all_permissions(university_network_group)
	if instance.state == MinutesDocument.PUBLISHED:
		assign_perm(instance.view_permission_name, student_group, instance)
		assign_perm(instance.view_permission_name, university_network_group, instance)
	if instance.state == MinutesDocument.PUBLISHED_STUDENT:
		assign_perm(instance.view_permission_name, student_group, instance)
		instance.delete_all_permissions(university_network_group)


class Guest(models.Model):
	name = models.CharField(max_length=255, verbose_name=_('Name'))
	minute = models.ForeignKey(MinutesDocument, on_delete=models.CASCADE, related_name='guests', verbose_name=_("Guests"))
