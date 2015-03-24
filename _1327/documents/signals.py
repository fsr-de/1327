from django.contrib.auth.models import Group
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils.text import slugify
from guardian.shortcuts import get_perms_for_model, assign_perm
from _1327.documents.models import Document


@receiver(pre_save)
def slugify_callback(sender, instance, *args, **kwargs):
	"""
		creates a slugified title that can be used as URL to the Document
		This will be used to identify a document that a user wants to see.
		In case someone creates a document with the same title it is not not defined
		which document might show up. So please try to avoid that ;)
	"""
	if sender not in Document.__subclasses__():
		return

	instance.url_title = slugify(instance.title)


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
