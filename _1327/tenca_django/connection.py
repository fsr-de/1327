import urllib.error

from django.core.exceptions import ImproperlyConfigured

from mailmanclient.restbase.connection import MailmanConnectionError

import tenca.connection


class FakeConnection:

	def __init__(self, exception):
		self.exception = exception

	def __getattr__(self, name):
		raise self.exception


try:
	connection = tenca.connection.Connection()
except (MailmanConnectionError, AttributeError) as e:
	connection = FakeConnection(ImproperlyConfigured(*e.args))
except urllib.error.HTTPError as e:
	connection = FakeConnection(ImproperlyConfigured(str(e)))
