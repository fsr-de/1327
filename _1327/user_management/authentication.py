from django.contrib.auth.models import Group
from django.contrib.auth import user_logged_in
from django.dispatch import receiver
from django.utils.translation import LANGUAGE_SESSION_KEY, get_language
from django.utils import translation
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

		if user_obj.is_authenticated:
			# user is not anonymous user and no other backend confirmed the permission yet
			# --> we need to check the anonymous permissions again
			check = ObjectPermissionChecker(get_anonymous_user())
			if check.has_perm(perm, obj):
				return True
		if group_name:
			group = Group.objects.get(name=group_name)
			check = ObjectPermissionChecker(group)
			return check.has_perm(perm, obj)
		return False


@receiver(user_logged_in)
def set_or_get_language(user, request, **kwargs):
	if user.language:
		print("Lang found:", user.language)
		request.session[LANGUAGE_SESSION_KEY] = user.language
		translation.activate(user.language)
	else:
		user.language = get_language()
		print("No lang found:", user.language)
		user.save()
