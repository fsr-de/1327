from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from guardian.shortcuts import get_perms


class IPRangeAuthorizationBackend:

	def authenticate(self, *args, **kwargs):
		return None

	def has_perm(self, user_obj, perm, obj=None):
		if obj is None:
			return False

		group_name = user_obj._ip_range_group_name if hasattr(user_obj, '_ip_range_group_name') else None
		if group_name:
			perm = perm.split(".")
			app = perm[0]
			perm = perm[1]

			# Only permissions from the same app as the object are valid.
			content_type = ContentType.objects.get_for_model(obj)
			if app != content_type.app_label:
				return False

			group = Group.objects.get(name=group_name)
			perms = get_perms(group, obj)
			return perm in perms
		return False
