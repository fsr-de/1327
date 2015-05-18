from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
import reversion
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

reversion.register(InformationDocument, follow=["document_ptr"])
