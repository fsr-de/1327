from django import template
from reversion import revisions

register = template.Library()


@register.filter
def num_revisions(document):
	versions = revisions.get_for_object(document)
	return len(versions)
