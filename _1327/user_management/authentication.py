from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from guardian.core import ObjectPermissionChecker
from guardian.utils import get_anonymous_user


class _1327AuthorizationBackend:

	def authenticate(self, *args, **kwargs):
		return None

	def has_perm(self, user_obj, perm, obj=None):
		if obj is None:
			return False

		app, perm = perm.split(".")

		# Only permissions from the same app as the object are valid.
		content_type = ContentType.objects.get_for_model(obj)
		if app != content_type.app_label:
			return False

		group_name = user_obj._ip_range_group_name if hasattr(user_obj, '_ip_range_group_name') else None

		has_perm = False
		if user_obj.is_authenticated():
			# user is not anonymous user and has no permissions on other elements
			# --> we need to check the anonymous permissions again
			check = ObjectPermissionChecker(get_anonymous_user())
			has_perm = check.has_perm(perm, obj)
		elif group_name:
			group = Group.objects.get(name=group_name)
			check = ObjectPermissionChecker(group)
			has_perm = check.has_perm(perm, obj)
		return has_perm
