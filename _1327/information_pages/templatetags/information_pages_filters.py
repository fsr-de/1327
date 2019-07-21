from django.template import Library

from _1327.information_pages.models import InformationDocument

register = Library()


@register.filter
def can_user_see_author(document, user):
	if document.show_author_to == InformationDocument.SHOW_AUTHOR_TO_EVERYONE:
		return True
	elif document.show_author_to == InformationDocument.SHOW_AUTHOR_TO_LOGGED_IN_USERS:
		return user.is_authenticated and not user.is_anonymous
	else:
		return False
