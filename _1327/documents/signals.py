from django.contrib.auth.models import Group
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from guardian.shortcuts import assign_perm, get_perms_for_model

from _1327.documents.models import Document
from _1327.main.utils import slugify


@receiver(pre_save)
def pre_save_document(sender, instance, *args, **kwargs):
	"""
		creates a slugified title that can be used as URL to the Document
		This will be used to identify a document that a user wants to see.
		In case someone creates a document with the same title it is not not defined
		which document might show up. So please try to avoid that ;)
	"""
	if sender not in Document.__subclasses__():
		return

	# get the max_length of a slug field as we need to make sure it is no longer than that
	# as slugify is not doing that for us
	for field in Document._meta.fields:
		if field.verbose_name == 'url_title' and instance.url_title == "":
			instance.url_title = slugify(instance.title)[:field.max_length]
			return


@receiver(post_save)
def permission_callback(sender, instance, created, *args, **kwargs):
	"""
		callback that assigns default permissions to the saved object
	"""

	if sender not in Document.__subclasses__() or not created:
		return

	permissions = get_perms_for_model(instance)
	groups = Group.objects.all()
	for group in groups:
		for permission in group.permissions.all():
			if permission in permissions:
				assign_perm(permission.codename, group, instance)
