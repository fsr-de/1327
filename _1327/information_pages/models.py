from django.core.urlresolvers import reverse
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.text import slugify
import reversion
from _1327.documents.models import Document


class InformationDocument(Document):

	class Meta:
		permissions = (
			('view_informationdocument', 'User/Group is allowed to view that information'),
		)


	def get_url(self):
		return reverse('information_pages:view_information', args=(self.url_title, ))

reversion.register(InformationDocument, follow=["document_ptr"])
