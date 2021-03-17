from django import template

register = template.Library()

@register.filter
def fqdn_ize(list_id):
	# template tags are loaded on django start-up, before a connection can be made
	from _1327.tenca_django.connection import connection
	return connection.fqdn_ize(list_id)
