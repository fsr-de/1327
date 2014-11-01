from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _
import reversion

from _1327.main.models import UserProfile


@reversion.register
class Document(models.Model):

	author = models.ForeignKey(UserProfile, related_name='documents')
	title = models.CharField(max_length=255)
	url_title = models.SlugField()
	text = models.TextField()
	type = models.CharField(max_length=5, default='I')

	types = (
		('I', _('Information')),
		('P', _('Protocol')),
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
