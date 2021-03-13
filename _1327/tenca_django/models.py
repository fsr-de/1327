from django.db import models
from tenca.hash_storage import (HashStorage, MailmanDescriptionHashStorage,
                                NotInStorageError, TwoLevelHashStorage)


class HashEntry(models.Model):
	hash_id = models.CharField(max_length=64, unique=True, blank=False, null=False)
	list_id = models.CharField(max_length=128, blank=False, null=False)


class LegacyAdminURL(models.Model):
	hash_id = models.ForeignKey(HashEntry,
		related_name='legacy_admin_url',
		on_delete=models.CASCADE
	)
	admin_url = models.CharField(max_length=32, blank=False, null=False)


class DjangoModelHashStorage(HashStorage):

	def __contains__(self, hash_id):
		try:
			HashEntry.objects.get(hash_id=hash_id)
			return True
		except HashEntry.DoesNotExist:
			return False

	def get_list_id(self, hash_id):
		try:
			entry = HashEntry.objects.get(hash_id=hash_id)
		except HashEntry.DoesNotExist:
			raise NotInStorageError()
		else:
			return entry.list_id

	def store_list_id(self, hash_id, list_id):
		entry = HashEntry(hash_id=hash_id, list_id=list_id)
		entry.save()

	def get_hash_id(self, list_id):
		try:
			entry = HashEntry.objects.get(list_id=list_id)
		except HashEntry.DoesNotExist:
			raise NotInStorageError()
		else:
			return entry.hash_id

	def delete_hash_id(self, hash_id):
		try:
			entry = HashEntry.objects.get(hash_id=hash_id)
		except HashEntry.DoesNotExist:
			pass
		else:
			entry.delete()

	def hashes(self):
		return (e.hash_id for e in HashEntry.objects.all())


class DjangoModelCachedDescriptionHashStorage(TwoLevelHashStorage):

	l1_class = DjangoModelHashStorage
	l2_class = MailmanDescriptionHashStorage
