from django.utils.translation import get_language


def translate(**kwargs):
	# Transforms everything that comes out of get_language to 'en' or 'de'. suffixes like -US are omitted.
	return property(lambda self: getattr(self, kwargs.get((get_language() or 'en').split('-')[0], 'en')))
