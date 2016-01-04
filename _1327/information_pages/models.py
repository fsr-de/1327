from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from reversion import revisions

from _1327.documents.models import Document


INFORMATIONDOCUMENT_VIEW_PERMISSION_NAME = 'view_informationdocument'


class InformationDocument(Document):
	VIEW_PERMISSION_NAME = INFORMATIONDOCUMENT_VIEW_PERMISSION_NAME

	class Meta(Document.Meta):
		verbose_name = _("Information document")
		verbose_name_plural = _("Information documents")
		permissions = (
			(INFORMATIONDOCUMENT_VIEW_PERMISSION_NAME, 'User/Group is allowed to view that document'),
		)

	def get_view_url(self):
		return reverse('information_pages:view_information', args=(self.url_title, ))

	def get_edit_url(self):
		return reverse('information_pages:edit', args=(self.url_title, ))

	def can_be_changed_by(self, user):
		permission_name = 'change_informationdocument'
		return user.has_perm(permission_name, self) or user.has_perm(permission_name)

revisions.register(InformationDocument, follow=["document_ptr"])
