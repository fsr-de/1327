from django.template import Library
from django.template.defaultfilters import floatformat

register = Library()


@register.filter(name='percentage')
def percentage(value):
	if value is None:
		return None
	return floatformat(value, 1) + '%'
