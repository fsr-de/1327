from django.contrib.auth.decorators import user_passes_test

def login_required(func):
	def check_user(user):
		return user.is_authenticated()
	return user_passes_test(check_user)(func)


def admin_required(func):
	def check_user(user):
		if not user.is_authenticated():
			return False
		return user.is_admin
	return user_passes_test(check_user)(func)
