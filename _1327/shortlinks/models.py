from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from _1327.documents.models import Document
from _1327.main.utils import slugify


class Shortlink(models.Model):
	url_title = models.CharField(unique=True, max_length=255, verbose_name=_("Url title"))
	link = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("External link"))
	document = models.ForeignKey(Document, blank=True, null=True, verbose_name=_("Document"), related_name='shortlinks')
	visit_count = models.IntegerField(default=0, verbose_name=_("Visit count"))
	created = models.DateTimeField(default=timezone.now, verbose_name=_("Last access"))
	last_access = models.DateTimeField(default=timezone.now, verbose_name=_("Last access"))

	def save(self, *args, **kwargs):
		# make sure that the url is slugified
		self.url_title = slugify(self.url_title)
		super().save(*args, **kwargs)
