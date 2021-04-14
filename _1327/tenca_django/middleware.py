import logging

from django.shortcuts import render

from _1327.tenca_django.connection import MailmanConnectionError

logger = logging.getLogger(__name__)


class TencaNoConnectionMiddleware:

	def __init__(self, get_response):
		self.get_response = get_response

	def __call__(self, request):
		return self.get_response(request)

	def process_exception(self, request, exception):
		if isinstance(exception, MailmanConnectionError):
			logger.error('An exception occurred when connecting to mailman: ' + ' '.join(map(str, exception.args)))
			return render(request, 'tenca_django/backend_error.html')
		else:
			return None
