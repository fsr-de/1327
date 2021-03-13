from django import template

from _1327.tenca_django import views

register = template.Library()

@register.filter
def fqdn_ize(list_id):
	return views.connection.fqdn_ize(list_id)

def deflate_attributes(attributes):
	return
