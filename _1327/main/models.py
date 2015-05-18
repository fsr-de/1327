from _1327.documents.models import Document
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.translation import ugettext_lazy as _


class MenuItem(models.Model):
	title = models.CharField(max_length=255, unique=False, verbose_name=_("Title"))
	order = models.IntegerField()

	link = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Link"))
	document = models.ForeignKey(Document, blank=True, null=True, verbose_name=_("Document"))

	parent = models.ForeignKey('self', blank=True, null=True, related_name='children')

	staff_only = models.BooleanField(default=False, verbose_name=_("Display for staff only"))

	class Meta:
		ordering = ['order']

	def __str__(self):
		return self.title

	def get_url(self):
		if self.link:
			return reverse(self.link)
		elif self.document:
			return self.document.get_view_url()

	def can_view(self, user):
		if user.is_superuser:
			return True

		if self.staff_only and not user.is_staff:
			return False

		if self.document:
			can_view_document = user.has_perm(self.document.get_view_permission())
			can_view_document |= user.has_perm(self.document.get_view_permission(), self.document)
			return can_view_document

		return True
