import urllib.error

from django.conf import settings as django_settings
from mailmanclient.restbase.connection import MailmanConnectionError

import tenca.connection
import tenca.settings


tenca.settings.load_from_module(django_settings)


class TencaNotConfiguredError(MailmanConnectionError):
	pass


class FakeConnection:

	def __init__(self, exception):
		self.exception = exception

	def __getattr__(self, name):
		raise self.exception


try:
	connection = tenca.connection.Connection()
except (MailmanConnectionError, AttributeError) as e:
	connection = FakeConnection(TencaNotConfiguredError(*e.args))
except urllib.error.HTTPError as e:
	connection = FakeConnection(TencaNotConfiguredError(str(e)))
