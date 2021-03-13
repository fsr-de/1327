from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext as _
from tenca import connection
from django.views.generic import TemplateView, FormView

from _1327.tenca_django.forms import TencaSubscriptionForm

connection = connection.Connection()

class TencaDashboard(TemplateView):
	template_name = "tenca_django/dashboard.html"


class TencaSubscriptionView(FormView):
	form_class = TencaSubscriptionForm
	template_name = "tenca_django/manage_subscription.html"

	def setup(self, request, *args, **kwargs):
		super().setup(request, *args, **kwargs)
		self.mailing_list = connection.get_list_by_hash_id(kwargs["hash_id"])
		if not self.mailing_list:
			raise Http404

	def get_context_data(self, **kwargs):
		kwargs.setdefault("list_name", self.mailing_list.fqdn_listname)
		return super().get_context_data(**kwargs)

	def form_valid(self, form):
		try:
			joined, token = self.mailing_list.toggle_membership(form.cleaned_data["email"])
			messages.success(self.request, _("The change has been requested. Please check your mails."))
			return redirect(reverse("tenca_django:tenca_dashboard"))
		except Exception as e:
			messages.error(self.request, _("An error occured: {error}").format(error=e))
			return self.render_to_response(self.get_context_data(form=form))
