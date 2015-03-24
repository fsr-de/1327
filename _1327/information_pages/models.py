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

	@receiver(pre_save)
	def slugify_callback(sender, instance, *args, **kwargs):
		"""
			creates a slugified title that can be used as URL to the Document
			This will be used to identify a document that a user wants to see.
			In case someone creates a document with the same title it is not not defined
			which document might show up. So please try to avoid that ;)
		"""
		if sender != InformationDocument:
			return

		instance.url_title = slugify(instance.title)

	def get_url(self):
		return reverse('information_pages:view_information', args=(self.url_title, ))

reversion.register(InformationDocument, follow=["document_ptr"])
