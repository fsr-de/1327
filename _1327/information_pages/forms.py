from django import forms
from django.conf import settings
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied

from _1327.documents.forms import DocumentForm
from .models import InformationDocument


class InformationDocumentForm(DocumentForm):
	class Meta(DocumentForm.Meta):
		model = InformationDocument
		fields = ['title', 'text', 'url_title', 'is_menu_page', 'comment']

	def __init__(self, *args, **kwargs):
		user = kwargs.pop('user', None)
		creation = kwargs.pop('creation', None)
		super().__init__(*args, **kwargs)
		staff = Group.objects.get(name=settings.STAFF_GROUP_NAME)

		if user.is_superuser:
			permitted_groups = Group.objects.filter(permissions__codename="add_informationdocument")
		else:
			permitted_groups = user.groups.filter(permissions__codename="add_informationdocument")
			if creation and permitted_groups.count() == 0:  # The user should not be able to view this form
				raise PermissionDenied

		self.fields['group'].queryset = permitted_groups.all()
		self.fields['group'].widget.attrs['class'] = 'select2-selection'
		if creation:
			if len(permitted_groups.all()) == 1:
				self.fields['group'].initial = permitted_groups.first()
				self.fields['group'].widget = forms.HiddenInput()
			elif staff in permitted_groups.all() and not self.fields['group'].initial:
				self.fields['group'].initial = staff
		else:
			self.fields['group'].widget = forms.HiddenInput()
			self.fields['group'].required = False


InformationDocument.Form = InformationDocumentForm
