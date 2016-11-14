from _1327.documents.forms import DocumentForm
from .models import InformationDocument


class InformationDocumentForm(DocumentForm):
	class Meta(DocumentForm.Meta):
		model = InformationDocument


InformationDocument.Form = InformationDocumentForm
