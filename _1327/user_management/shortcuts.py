from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404


def get_object_or_error(klass, user, permissions, *args, **kwargs):
	"""
		tries to get the object the user wants and checks whether the user is allowed to use this object
		make sure to provide the permission in the following format: appname.codename
		i.e. documents.change_document if user needs to be allowed to change a document
	"""
	obj = get_object_or_404(klass, *args, **kwargs)

	for permission in permissions:
		# first check for global permission
		if user.has_perm(permission):
			continue

		# check for object level permission
		if not user.has_perm(permission, obj):
			raise PermissionDenied
	return obj


