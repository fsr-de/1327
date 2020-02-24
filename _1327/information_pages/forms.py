from _1327.documents.forms import DocumentForm
from .models import InformationDocument


class InformationDocumentForm(DocumentForm):
	class Meta(DocumentForm.Meta):
		model = InformationDocument
		fields = ['title_de', 'title_en', 'text_de', 'text_en', 'url_title', 'is_menu_page', 'comment']


InformationDocument.Form = InformationDocumentForm
