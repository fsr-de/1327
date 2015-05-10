from django.contrib.contenttypes.models import ContentType
from django.db import models
from polymorphic import PolymorphicModel

import reversion

from _1327.user_management.models import UserProfile


DOCUMENT_VIEW_PERMISSION_NAME = 'view_document'


@reversion.register
class Document(PolymorphicModel):
	created = models.DateTimeField(auto_now_add=True)
	author = models.ForeignKey(UserProfile, related_name='documents')
	title = models.CharField(max_length=255)
	url_title = models.SlugField()
	text = models.TextField()
	initial = models.BooleanField(default=True)  # whether the document was just created and not yet manually saved

	VIEW_PERMISSION_NAME = DOCUMENT_VIEW_PERMISSION_NAME

	class Meta:
		permissions = (
			(DOCUMENT_VIEW_PERMISSION_NAME, 'User/Group is allowed to view that document'),
		)

	def __str__(self):
		return self.title

	def get_url(self):
		raise NotImplementedError()

	@classmethod
	def get_view_permission(klass):
		content_type = ContentType.objects.get_for_model(klass)
		app_label = content_type.app_label
		permission = "{}.{}".format(app_label, klass.VIEW_PERMISSION_NAME)
		return permission


class TemporaryDocumentText(models.Model):
	text = models.TextField()
	document = models.ForeignKey(Document, related_name='document')
	created = models.DateTimeField(auto_now=True)


class Attachment(models.Model):

	displayname = models.TextField(max_length=255, blank=True, default="")
	document = models.ForeignKey(Document, related_name='attachments')
	created = models.DateTimeField(auto_now=True)
	file = models.FileField(upload_to="documents/%y/%m/")
