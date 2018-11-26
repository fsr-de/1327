from django.utils.translation import get_language


def translate(**kwargs):
	# get_language may return None if there is no session (e.g. during management commands)
	language_code = get_language()
	if language_code is not None and language_code.startswith("de"):
		code = "de"
	else:
		code = "en"

	return property(lambda self: getattr(self, kwargs[code]))
