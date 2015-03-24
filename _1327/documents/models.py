from django.db import models
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
			('view_document', 'User/Group is allowed to view that document'),
		)

	def __str__(self):
		return self.title


class TemporaryDocumentText(models.Model):
	text = models.TextField()
	document = models.ForeignKey(Document, related_name='document')
	created = models.DateTimeField(auto_now=True)
