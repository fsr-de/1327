from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied


def login_required(func):
	def check_user(user):
		return user.is_authenticated()
	return user_passes_test(check_user)(func)


def admin_required(func):
	def check_user(user):
		if not user.is_authenticated():
			return False
		if not user.is_admin:
			raise PermissionDenied
		return True
	return user_passes_test(check_user)(func)
