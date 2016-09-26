from django.core.exceptions import PermissionDenied


def check_permissions(obj, user, permissions):
	"""
		checks whether user has all necessary permissions necessary for working with that object
		raises PermissionDenied if permissions are not sufficient, otherwise it silently returns
	"""
	for permission in permissions:
		# first check for global permission
		if user.has_perm(permission):
			continue

		# check for object level permission
		if not user.has_perm(permission, obj):
			raise PermissionDenied
