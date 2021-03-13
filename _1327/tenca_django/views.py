from tenca import connection
from tenca.exceptions import NoSuchRequestException
from django.contrib import messages
from django.http import Http404
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView
from urllib.parse import urljoin

import tenca
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views import View
from tenca import connection, pipelines
from django.views.generic import TemplateView, FormView

from _1327.tenca_django.forms import TencaSubscriptionForm, TencaNewListForm, TencaListOptionsForm

connection = connection.Connection()


class TencaDashboard(LoginRequiredMixin, FormView):
	template_name = "tenca_django/dashboard.html"
	form_class = TencaNewListForm

	def get_context_data(self, **kwargs):
		kwargs.setdefault("memberships", connection.get_owner_and_memberships(self.request.user.email))
		return super().get_context_data(**kwargs)

	def form_valid(self, form):
		try:
			new_list = connection.add_list(form.cleaned_data["list_name"], self.request.user.email)
			messages.success(self.request, _("The list {list} has been created successfully.").format(list=new_list.fqdn_listname))
			return redirect("tenca_django:tenca_dashboard")
		except Exception as e:
			messages.error(self.request, _("An error occurred: {error}").format(error=e))
			return self.render_to_response(self.get_context_data(form=form))


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

	def get_form_kwargs(self):
		return dict(initial={"email": self.request.user.email})

	def form_valid(self, form):
		try:
			joined, token = self.mailing_list.toggle_membership(form.cleaned_data["email"])
			messages.success(self.request, _("The change has been requested. Please check your mails."))
			return redirect(reverse("tenca_django:tenca_dashboard"))
		except Exception as e:
			messages.error(self.request, _("An error occurred: {error}").format(error=e))
			return self.render_to_response(self.get_context_data(form=form))


class TencaListAdminView(LoginRequiredMixin, FormView):
	template_name = "tenca_django/manage_list.html"

	def setup(self, request, *args, **kwargs):
		super().setup(request, *args, **kwargs)
		self.mailing_list = connection.get_list(kwargs["list_id"])
		if not self.mailing_list:
			raise Http404

	def get_form(self, form_class=None):
		return TencaListOptionsForm(self.request.POST or None, mailing_list=self.mailing_list)

	def get_context_data(self, **kwargs):
		kwargs.setdefault("mailing_list", self.mailing_list)
		kwargs.setdefault("listname", self.mailing_list.fqdn_listname)
		# kwargs.setdefault("invite_link", urljoin("https://" + settings.PAGE_URL, reverse("tenca_django:tenca_manage_subscription", kwargs=dict(hash_id=self.mailing_list.hash_id))))
		kwargs.setdefault("invite_link", pipelines.call_func(tenca.settings.BUILD_INVITE_LINK, self.mailing_list))
		return super().get_context_data(**kwargs)

	def form_valid(self, form):
		for key, value in form.cleaned_data.items():
			setattr(self.mailing_list, key, value)
		messages.success(self.request, _("List options saved successfully."))
		return redirect(reverse("tenca_django:tenca_manage_list", kwargs=dict(list_id=self.mailing_list.list_id)))


class TencaMemberEditView(LoginRequiredMixin, View):
	def post(self, request, *args, **kwargs):
		pass

def lookup_list_and_email(list_id, token):
	mailing_list = connection.get_list(list_id)
	if mailing_list is None:
		raise Http404("This link is invalid.")

	return (mailing_list, mailing_list.pending_subscriptions().get(token))

def confirm(request, list_id, token):
	mailing_list, email = lookup_list_and_email(list_id, token)

	try:
		mailing_list.confirm_subscription(token)
	except NoSuchRequestException:
		raise Http404("This link is invalid.")

	if email is not None:
		connection.mark_address_verified(email)
		messages.success(request, _("{} has successfully joined {}.").format(email, mailing_list.fqdn_listname))
	else:
		messages.success(request, _("You have successfully left {}.").format(mailing_list.fqdn_listname))

	return render(request, "tenca_django/action.html", {
		'list_id': list_id,
		'token': token,
	})

def report(request, list_id, token):
	mailing_list, email = lookup_list_and_email(list_id, token)

	try:
		mailing_list.cancel_pending_subscription(token)
		messages.success(request, _("The subscription of {} onto {} was rolled back.").format(email, mailing_list.fqdn_listname))
	except NoSuchRequestException:
		pass # We don't tell to leak no data

	return render(request, "tenca_django/report.html", {})
