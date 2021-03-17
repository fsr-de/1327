import tenca.settings
from django.conf import settings as django_settings

tenca.settings.load_from_module(django_settings)

from mailmanclient.restbase.connection import MailmanConnectionError
import tenca.connection

from logging import Logger

logger = Logger(__name__)

try:
	connection = tenca.connection.Connection()
except MailmanConnectionError as e:
	from django.utils.translation import gettext_lazy as _
	logger.warn(_("No connection to mailman available. Please fix your firewall rules/config and restart the 1327 service."))

	class FakeConnection:

		def __init__(self, e):
			self.e = e

		def __getattr__(self, name):
			raise self.e

	connection = FakeConnection(e)

