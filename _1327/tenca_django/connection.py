import urllib.error

from mailmanclient.restbase.connection import MailmanConnectionError

import tenca.connection


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
