from django.utils.translation import get_language


def translate(**kwargs):
	# get_language may return None if there is no session (e.g. during management commands)
	return property(lambda self: getattr(self, kwargs[get_language() or 'en']))
