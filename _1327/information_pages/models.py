from django.core.urlresolvers import reverse
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.text import slugify
import reversion
from _1327.documents.models import Document


INFORMATIONDOCUMENT_VIEW_PERMISSION_NAME = 'view_informationdocument'


class InformationDocument(Document):

	VIEW_PERMISSION_NAME = INFORMATIONDOCUMENT_VIEW_PERMISSION_NAME

	class Meta(Document.Meta):
		permissions = (
			(INFORMATIONDOCUMENT_VIEW_PERMISSION_NAME, 'User/Group is allowed to view that document'),
		)


	def get_url(self):
		return reverse('information_pages:view_information', args=(self.url_title, ))

reversion.register(InformationDocument, follow=["document_ptr"])
