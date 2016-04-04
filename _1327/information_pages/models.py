from django.core.urlresolvers import reverse
from django.template import Context, loader
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
		return reverse('documents:view', args=(self.url_title, ))

	def get_edit_url(self):
		return reverse('documents:edit', args=(self.url_title, ))

	def can_be_changed_by(self, user):
		permission_name = 'change_informationdocument'
		return user.has_perm(permission_name, self) or user.has_perm(permission_name)

	@property
	def meta_information_html(self):
		template = loader.get_template('information_pages_meta_information.html')
		return template.render(Context({'document': self}))

revisions.register(InformationDocument, follow=["document_ptr"])
