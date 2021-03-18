from django.contrib import messages
from django.shortcuts import render
from django.utils.translation import gettext as _

from _1327.tenca_django.connection import MailmanConnectionError, TencaNotConfiguredError


class TencaNoConnectionMiddleware:

	def __init__(self, get_response):
		self.get_response = get_response

	def __call__(self, request):
		return self.get_response(request)

	def process_exception(self, request, exception):
		if isinstance(exception, MailmanConnectionError):
			if isinstance(exception, TencaNotConfiguredError):
				messages.error(request, _("Mailing lists misconfigured. {error}").format(error=" ".join(map(str, exception.args))))
			return render(request, 'tenca_django/backend_error.html')
		else:
			return None
