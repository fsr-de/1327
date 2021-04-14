from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic import FormView, RedirectView, TemplateView

import tenca.exceptions
import tenca.pipelines
import tenca.settings

from _1327.main.utils import alternative_emails
from _1327.tenca_django.connection import connection
from _1327.tenca_django.forms import TencaListOptionsForm, TencaMemberEditForm, TencaNewListForm, TencaSubscriptionForm
from _1327.tenca_django.mixins import TencaListAdminMixin, TencaSingleListMixin
from _1327.tenca_django.models import LegacyAdminURL


class TencaDashboard(LoginRequiredMixin, FormView):
	template_name = "tenca_django/dashboard.html"
	form_class = TencaNewListForm

	def get_context_data(self, **kwargs):
		email = self.request.user.email
		kwargs.setdefault("memberships", connection.get_owner_and_memberships(email, *alternative_emails(email)))
		kwargs.setdefault("domain_addon", "@" + str(connection.domain))
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

	def get_initial(self):
		return {"email": self.request.user.email if self.request.user.is_authenticated else None}

	def form_valid(self, form):
		try:
			joined, token = self.mailing_list.toggle_membership(form.cleaned_data["email"])
			messages.success(self.request, _("The change has been requested. Please check your mails."))
			return redirect(reverse("tenca_django:tenca_dashboard"))
		except Exception as e:
			messages.error(self.request, _("An error occurred: {error}").format(error=e))
			return self.render_to_response(self.get_context_data(form=form))


class TencaListAdminView(TencaListAdminMixin, LoginRequiredMixin, FormView):
	template_name = "tenca_django/manage_list.html"

	def get_form(self, form_class=None):
		return TencaListOptionsForm(self.request.POST or None, mailing_list=self.mailing_list)

	def get_context_data(self, **kwargs):
		kwargs.setdefault("mailing_list", self.mailing_list)
		kwargs.setdefault("listname", self.mailing_list.fqdn_listname)
		# kwargs.setdefault("invite_link", urllib.parse.urljoin("https://" + settings.PAGE_URL, reverse("tenca_django:tenca_manage_subscription", kwargs=dict(hash_id=self.mailing_list.hash_id))))
		kwargs.setdefault("invite_link", tenca.pipelines.call_func(tenca.settings.BUILD_INVITE_LINK, self.mailing_list))
		kwargs.setdefault("members", [(TencaMemberEditForm(initial=dict(email=address)), is_owner, is_blocked) for (address, (is_owner, is_blocked)) in self.mailing_list.get_roster()])
		return super().get_context_data(**kwargs)

	def form_valid(self, form):
		for key, value in form.cleaned_data.items():
			setattr(self.mailing_list, key, value)
		messages.success(self.request, _("List options saved successfully."))
		return redirect(reverse("tenca_django:tenca_manage_list", kwargs=dict(list_id=self.mailing_list.list_id)))


class TencaMemberEditView(TencaListAdminMixin, LoginRequiredMixin, View):
	def post(self, request, *args, **kwargs):
		form = TencaMemberEditForm(self.request.POST)
		if form.is_valid():
			operations = [
				('remove_member', self.mailing_list.remove_member_silently, _('Removed {member}')),
				('promote_member', self.mailing_list.promote_to_owner, _('Promoted {member}')),
				('demote_member', self.mailing_list.demote_from_owner, _('Demoted {member}')),
				('block_member', lambda a: self.mailing_list.set_blocked(a, True), _('Blocked {member}')),
				('unblock_member', lambda a: self.mailing_list.set_blocked(a, False), _('Unblocked {member}')),
			]
			for (name, func, success_string) in operations:
				if name in request.POST:
					try:
						func(form.cleaned_data["email"])
						messages.success(request, success_string.format(member=form.cleaned_data["email"]))
					except Exception as e:
						messages.error(request, _("An error occurred: {error}").format(error=e))
						return redirect(reverse("tenca_django:tenca_manage_list", kwargs=dict(list_id=self.mailing_list.list_id)))

			if request.user.email == form.cleaned_data["email"] and any(
				x in request.POST for x in ['remove_member', 'demote_member']):
				# If you demote yourself, you cannot access the admin page anymore
				return redirect(reverse("tenca_django:tenca_dashboard"))

			return redirect(reverse("tenca_django:tenca_manage_list", kwargs=dict(list_id=self.mailing_list.list_id)))


class TencaListDeleteView(TencaListAdminMixin, LoginRequiredMixin, TemplateView):
	template_name = "tenca_django/delete_list.html"

	def get_context_data(self, **kwargs):
		kwargs.setdefault("listname", self.mailing_list.fqdn_listname)
		kwargs.setdefault("mailing_list", self.mailing_list)
		return super().get_context_data(**kwargs)

	def post(self, request, *args, **kwargs):
		if "confirm" in request.POST:
			try:
				connection.delete_list(self.mailing_list.fqdn_listname)
				messages.success(request, _("{list} has been deleted successfully.").format(list=self.mailing_list.fqdn_listname))
				return redirect(reverse("tenca_django:tenca_dashboard"))
			except Exception as e:
				messages.error(request, _("An error occurred: {error}").format(error=e))
				return redirect(reverse("tenca_django:tenca_manage_list", kwargs=dict(list_id=self.mailing_list.list_id)))
		return self.render_to_response(self.get_context_data())


class TencaActionConfirmView(TencaSingleListMixin, TemplateView):
	template_name = "tenca_django/action.html"

	def get_context_data(self, **kwargs):
		try:
			email, join = self.mailing_list.pending_subscriptions().get(kwargs.get("token")), True
			if email is None:
				email, join = self.mailing_list.pending_subscriptions('unsubscription').get(kwargs.get("token")), False
				if self.mailing_list.is_owner(email):
					self.mailing_list.demote_from_owner(email)

			self.mailing_list.confirm_subscription(kwargs.get("token"))
		except tenca.exceptions.NoSuchRequestException:
			raise Http404("This link is invalid.")
		except tenca.exceptions.LastOwnerException:
			messages.error(self.request, _("{email} is the last owner of {list}. Please delegate your job first, before leaving the list.").format(email=email, list=self.mailing_list.fqdn_listname))
			try:
				self.mailing_list.cancel_pending_subscription(kwargs.get("token"))
			except tenca.exceptions.NoSuchRequestException:
				pass
			return super().get_context_data(**kwargs)

		if join is True:
			connection.mark_address_verified(email)
			messages.success(self.request, _("{email} has successfully joined {list}.").format(email=email, list=self.mailing_list.fqdn_listname))
		else:
			messages.success(self.request, _("{email} has successfully left {list}.").format(email=email, list=self.mailing_list.fqdn_listname))
		kwargs.setdefault("list_id", self.mailing_list.list_id)
		return super().get_context_data(**kwargs)


class TencaReportView(TencaSingleListMixin, TemplateView):
	template_name = "tenca_django/report.html"

	def get_context_data(self, **kwargs):
		email = self.mailing_list.pending_subscriptions().get(kwargs.get("token"))
		try:
			self.mailing_list.cancel_pending_subscription(kwargs.get("token"))
			messages.success(self.request, _("The subscription of {email} onto {list} was rolled back.").format(email=email, list=self.mailing_list.fqdn_listname))
		except tenca.exceptions.NoSuchRequestException:
			pass  # We don't tell to leak no data
		return super().get_context_data(**kwargs)


class TencaLegacyAdminLinkView(LoginRequiredMixin, RedirectView):
	def get_redirect_url(self, *args, **kwargs):
		try:
			LegacyAdminURL.objects.get(hash_id__hash_id=kwargs.get("hash_id"), admin_url=kwargs.get("admin_url"))
			mailing_list = connection.get_list_by_hash_id(kwargs.get("hash_id"))
			if mailing_list is None:
				raise Http404
			if self.request.user.is_staff:
				messages.warning(self.request, _("Please manage this list from the admin interface. This link will stop working in the future."))
			else:
				user_email = self.request.user.email
				if not mailing_list.is_member(user_email):
					mailing_list.add_member_silently(user_email)
				if not mailing_list.is_owner(user_email):
					mailing_list.promote_to_owner(user_email)
					messages.success(self.request, _("You have been promoted to a list owner. From now on, you can manage this list from your dashboard. This link is obsolete."))
				else:
					messages.warning(self.request, _("You are already a list owner and can manage this list from you dashboard. This link will stop working in the future."))
			return reverse("tenca_django:tenca_manage_list", kwargs=dict(list_id=mailing_list.list_id))
		except LegacyAdminURL.DoesNotExist:
			raise Http404
