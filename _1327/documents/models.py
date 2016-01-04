from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import ugettext_lazy as _
from polymorphic.models import PolymorphicModel

from reversion import revisions

from _1327.user_management.models import UserProfile


DOCUMENT_VIEW_PERMISSION_NAME = 'view_document'


@revisions.register
class Document(PolymorphicModel):
	created = models.DateTimeField(auto_now_add=True)
	title = models.CharField(max_length=255)
	url_title = models.SlugField()
	text = models.TextField()

	VIEW_PERMISSION_NAME = DOCUMENT_VIEW_PERMISSION_NAME

	class Meta:
		verbose_name = _("Document")
		verbose_name_plural = _("Documents")
		permissions = (
			(DOCUMENT_VIEW_PERMISSION_NAME, 'User/Group is allowed to view that document'),
		)

	def __str__(self):
		return self.title

	def get_view_url(self):
		raise NotImplementedError()

	def get_edit_url(self):
		raise NotImplementedError()

	@classmethod
	def get_view_permission(klass):
		content_type = ContentType.objects.get_for_model(klass)
		app_label = content_type.app_label
		permission = "{}.{}".format(app_label, klass.VIEW_PERMISSION_NAME)
		return permission

	def can_be_changed_by(self, user):
		raise NotImplementedError

	def authors(self):
		authors = set()
		versions = revisions.get_for_object(self)
		for version in versions:
			authors.add(version.revision.user)
		return authors


class TemporaryDocumentText(models.Model):
	text = models.TextField()
	document = models.ForeignKey(Document, related_name='document')
	created = models.DateTimeField(auto_now=True)
	author = models.ForeignKey(UserProfile, related_name='temporary_documents')


class Attachment(models.Model):
	displayname = models.TextField(max_length=255, blank=True, default="", verbose_name=_("Display name"))
	document = models.ForeignKey(Document, related_name='attachments', verbose_name=_("Document"))
	created = models.DateTimeField(auto_now=True, verbose_name=_("Created"))
	file = models.FileField(upload_to="documents/%y/%m/", verbose_name=_("File"))

	index = models.IntegerField(verbose_name=_("ordering index"), default=0)
	no_direct_download = models.BooleanField(default=False, verbose_name=_("Do not show as attachment (for embedded images)"))

	class Meta:
		verbose_name = _("Attachment")
		verbose_name_plural = _("Attachments")
