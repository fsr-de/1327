import unicodedata

from django.contrib.auth import user_logged_in
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.dispatch import receiver
from django.utils import translation
from django.utils.translation import get_language, LANGUAGE_SESSION_KEY
from guardian.core import ObjectPermissionChecker
from guardian.utils import get_anonymous_user
from mozilla_django_oidc.auth import OIDCAuthenticationBackend

from _1327.main.utils import clean_email
from _1327.user_management.models import UserProfile


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
		request.session[LANGUAGE_SESSION_KEY] = user.language
		translation.activate(user.language)
	else:
		user.language = get_language()
		user.save()


# see https://mozilla-django-oidc.readthedocs.io/en/stable/
class OpenIDAuthenticationBackend(OIDCAuthenticationBackend):
	def filter_users_by_claims(self, claims):
		email = claims.get('email')
		if not email:
			return []

		try:
			return [UserProfile.objects.get(email=clean_email(email))]
		except UserProfile.DoesNotExist:
			return []

	def create_user(self, claims):
		user = UserProfile.objects.create(
			username=generate_username_from_email(claims.get('email')),
			email=claims.get('email'),
			first_name=claims.get('given_name', ''),
			last_name=claims.get('family_name', ''),
		)
		return user


def generate_username_from_email(email):
	return unicodedata.normalize('NFKC', email).split('@')[0].lower()
