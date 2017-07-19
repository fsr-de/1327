from django import forms
from django.conf import settings
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied, ValidationError
from django.forms import inlineformset_factory
from django.utils.translation import ugettext_lazy as _

from _1327.documents.forms import AtLeastNFormSet, DocumentForm
from .models import Choice, Poll


class PollForm(DocumentForm):
	vote_groups = forms.ModelMultipleChoiceField(Group.objects.exclude(name=settings.ANONYMOUS_GROUP_NAME).exclude(name=settings.UNIVERSITY_GROUP_NAME), label=_('Vote permissions'), disabled=False, required=False)

	class Meta:
		model = Poll
		fields = ['title', 'url_title', 'text', 'start_date', 'end_date', 'max_allowed_number_of_answers', 'show_results_immediately', 'comment', 'group', 'vote_groups']

	def __init__(self, *args, **kwargs):
		user = kwargs.pop('user', None)
		creation = kwargs.pop('creation', None)
		kwargs.pop('creation_group', None)
		super().__init__(*args, **kwargs)
		staff = Group.objects.get(name=settings.STAFF_GROUP_NAME)

		if user.is_superuser:
			permitted_groups = Group.objects.filter(permissions__codename="add_poll")
		else:
			permitted_groups = user.groups.filter(permissions__codename="add_poll")

		if permitted_groups.count() == 0:  # The user should not be able to view this form
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

		if creation:
			self.fields['vote_groups'].widget.attrs['class'] = 'select2-selection'
		else:
			self.fields['vote_groups'].widget = forms.HiddenInput()
			self.fields['vote_groups'].required = False

	def clean(self):
		super().clean()
		start_date = self.cleaned_data.get('start_date')
		end_date = self.cleaned_data.get('end_date')
		if start_date and end_date:
			if start_date > end_date:
				self.add_error('start_date', forms.ValidationError(_("The start date must be before or on the end date.")))

	@classmethod
	def get_formset_factory(cls):
		return inlineformset_factory(
			Poll,
			Choice,
			form=ChoiceForm,
			extra=1,
			can_delete=True,
			min_num=2,
			validate_min=True,
			formset=AtLeastNFormSet,
		)

	def clean_vote_groups(self):
		groups = self.cleaned_data['vote_groups']
		for group in groups:
			if group.name == settings.ANONYMOUS_GROUP_NAME or group.name == settings.UNIVERSITY_GROUP_NAME:
				raise ValidationError(_("Anonymous and university network groups are not allowed to vote!"))
		return groups


Poll.Form = PollForm


class ChoiceForm(forms.ModelForm):
	class Meta:
		model = Choice
		exclude = ["poll", "votes"]
		widgets = {
			"description": forms.TextInput(),
			"index": forms.HiddenInput(),
		}
