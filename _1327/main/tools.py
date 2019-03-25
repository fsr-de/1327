from django.utils.translation import get_language


def translate(**kwargs):
	return property(lambda self: getattr(self, kwargs[(get_language() or 'en').split('-')[0]]))
