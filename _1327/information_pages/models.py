from django.db import models
from django.template import loader
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from reversion import revisions

from _1327.documents.models import Document

INFORMATIONDOCUMENT_VIEW_PERMISSION_NAME = 'view_informationdocument'


class InformationDocument(Document):
	VIEW_PERMISSION_NAME = INFORMATIONDOCUMENT_VIEW_PERMISSION_NAME

	is_menu_page = models.BooleanField(default=False, verbose_name=_("Is menu page"), help_text=_("Select this if the page is used mainly for navigation purposes and if all documents linked on the page should be removed from the 'unlinked information pages' list."))

	class Meta(Document.Meta):

		verbose_name = _("Information document")
		verbose_name_plural = _("Information documents")
		permissions = (
			(INFORMATIONDOCUMENT_VIEW_PERMISSION_NAME, 'User/Group is allowed to view that document'),
		)

	def get_view_url(self):
		return reverse(self.get_view_url_name(), args=(self.url_title, ))

	def get_edit_url(self):
		return reverse(self.get_edit_url_name(), args=(self.url_title, ))

	def can_be_changed_by(self, user):
		permission_name = self.edit_permission_name
		return user.has_perm(permission_name, self) or user.has_perm(permission_name)

	@property
	def meta_information_html(self):
		return loader.get_template('information_pages_meta_information.html')


revisions.register(InformationDocument, follow=["document_ptr"])
