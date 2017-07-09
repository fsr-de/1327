from django import template
from reversion.models import Version

register = template.Library()


@register.filter
def num_revisions(document):
	versions = Version.objects.get_for_object(document)
	return len(versions)
