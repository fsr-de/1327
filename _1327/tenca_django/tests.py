from django.test import TestCase

from tenca.tests import test_hash_storage
from _1327.tenca_django.models import DjangoModelHashStorage

class DjangoModelHashStorageTest(TestCase, test_hash_storage.HiddenFromTestRunner.HashStorageTest):
	StorageClass = DjangoModelHashStorage
