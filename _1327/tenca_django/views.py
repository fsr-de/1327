from tenca import connection
from tenca.exceptions import NoSuchRequestException
from django.contrib import messages
from django.http import Http404
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

connection = connection.Connection()

class TencaDashboard(TemplateView):
	template_name = "tenca_django/dashboard.html"

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