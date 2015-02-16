from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.template.defaultfilters import slugify
from polymorphic import PolymorphicModel
import reversion

from _1327.user_management.models import UserProfile


@reversion.register
class Document(PolymorphicModel):

	author = models.ForeignKey(UserProfile, related_name='documents')
	title = models.CharField(max_length=255)
	url_title = models.SlugField()
	text = models.TextField()

	class Meta:
		permissions = (
			('view_document', 'User/Group is allowed to View that Document'),
		)

	@receiver(pre_save)
	def slugify_callback(sender, instance, *args, **kwargs):
		"""
			creates a slugified title that can be used as URL to the Document
			This will be used to identify a document that a user wants to see.
			In case someone creates a document with the same title it is not not defined
			which document might show up. So please try to avoid that ;)
		"""
		if sender != Document:
			return

		instance.url_title = slugify(instance.title)

	def __str__(self):
		return self.title

class TemporaryDocumentText(models.Model):
	text = models.TextField()
	document = models.ForeignKey(Document, related_name='document')
	created = models.DateTimeField(auto_now=True)
