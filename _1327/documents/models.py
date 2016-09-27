from datetime import datetime

from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from guardian.shortcuts import assign_perm, get_groups_with_perms, get_users_with_perms, remove_perm
from polymorphic.models import PolymorphicModel
from reversion import revisions

from _1327.documents.markdown_internal_link_pattern import InternalLinkPattern
from _1327.user_management.models import UserProfile


DOCUMENT_VIEW_PERMISSION_NAME = 'view_document'


@revisions.register
class Document(PolymorphicModel):
	created = models.DateTimeField(default=timezone.now)
	title = models.CharField(max_length=255)
	url_title = models.SlugField(unique=True)
	text = models.TextField()

	DOCUMENT_LINK_REGEX = r'\[(?P<title>[^\[]+)\]\(document:(?P<id>\d+)\)'
	VIEW_PERMISSION_NAME = DOCUMENT_VIEW_PERMISSION_NAME

	class Meta:
		verbose_name = _("Document")
		verbose_name_plural = _("Documents")
		permissions = (
			(DOCUMENT_VIEW_PERMISSION_NAME, 'User/Group is allowed to view that document'),
		)

	class LinkPattern (InternalLinkPattern):

		def url(self, id):
			document = Document.objects.get(id=id)
			if document:
				return reverse('documents:view', args=[document.url_title])
			return ''

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

	def save_formset(self, formset):
		pass

	def can_be_changed_by(self, user):
		raise NotImplementedError

	def authors(self):
		authors = set()
		versions = revisions.get_for_object(self)
		for version in versions:
			authors.add(version.revision.user)
		return authors

	@classmethod
	def generate_new_title(cls):
		return _("New Page from {}").format(str(datetime.now()))

	@classmethod
	def generate_default_slug(cls, title):
		return slugify(title)

	@property
	def view_permission_name(self):
		content_type = ContentType.objects.get_for_model(self)
		return "{app}.view_{model}".format(app=content_type.app_label, model=content_type.model)

	@property
	def edit_permission_name(self):
		content_type = ContentType.objects.get_for_model(self)
		return "{app}.change_{model}".format(app=content_type.app_label, model=content_type.model)

	@property
	def add_permission_name(self):
		content_type = ContentType.objects.get_for_model(self)
		return "{app}.add_{model}".format(app=content_type.app_label, model=content_type.model)

	@property
	def delete_permission_name(self):
		content_type = ContentType.objects.get_for_model(self)
		return "{app}.delete_{model}".format(app=content_type.app_label, model=content_type.model)

	def delete_all_permissions(self, user_or_group):
		remove_perm(self.view_permission_name, user_or_group, self)
		remove_perm(self.edit_permission_name, user_or_group, self)
		remove_perm(self.delete_permission_name, user_or_group, self)

	def set_all_permissions(self, user_or_group):
		assign_perm(self.view_permission_name, user_or_group, self)
		assign_perm(self.edit_permission_name, user_or_group, self)
		assign_perm(self.delete_permission_name, user_or_group, self)

	def reset_permissions(self):
		users = get_users_with_perms(self)
		for user in users:
			self.delete_all_permissions(user)
		groups = get_groups_with_perms(self)
		for group in groups:
			self.delete_all_permissions(group)

	@property
	def meta_information_html(self):
		raise NotImplementedError('Please use a subclass of Document')

	@property
	def last_change(self):
		last_revision = revisions.get_for_object(self).order_by('revision__date_created').last()
		if last_revision is None:
			return None
		return last_revision.revision.date_created

	def show_permissions_editor(self):
		return True

	def show_publish_button(self):
		return False

	def has_perms(self):
		group_perms = get_groups_with_perms(self, attach_perms=True)
		content_type = ContentType.objects.get_for_model(self)
		for perms in group_perms.values():
			for perm in perms:
				perm = "{app}.{perm}".format(app=content_type.app_label, perm=perm)
				if perm != self.add_permission_name:
					return True
		return False

	def handle_edit(self, cleaned_data):
		pass


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
