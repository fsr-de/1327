from django.template import Library

from _1327.information_pages.models import InformationDocument

register = Library()


@register.assignment_tag(takes_context=True)
def resolve_show_author_policy(context, show_author_to):
	if show_author_to == InformationDocument.SHOW_AUTHOR_TO_EVERYONE:
		return True
	elif show_author_to == InformationDocument.SHOW_AUTHOR_TO_LOGGED_IN_USERS:
		return context['request'].user.is_authenticated()
	else:
		return False
