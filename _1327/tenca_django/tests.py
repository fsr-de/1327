import unittest

from django.conf import settings
from django.test import TestCase

from tenca.tests import test_hash_storage

from _1327.tenca_django.models import DjangoModelHashStorage


def skipUnlessListsEnabled():
	if not settings.ENABLE_MAILING_LISTS:
		return unittest.skip('Mailing lists not enabled in Django settings')

	return lambda x: x


@skipUnlessListsEnabled()
class TencaSettingsLoaded(TestCase):

	def setUp(self):
		from _1327.tenca_django.connection import connection
		self.connection = connection

	def testConnectionReceivedSettings(self):
		self.assertEqual(settings.TENCA_TEST_LIST_DOMAIN, str(self.connection.domain))


@skipUnlessListsEnabled()
class DjangoModelHashStorageTest(TestCase, test_hash_storage.HiddenFromTestRunner.HashStorageTest):
	StorageClass = DjangoModelHashStorage
