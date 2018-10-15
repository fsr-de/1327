from django.template import Library

register = Library()


@register.simple_tag(name='redirect_login', takes_context=True)
def redirect_login(context):
	request = getattr(context, 'request', None)
	if request is None:
		path = '/'
	else:
		path = request.path
	return "?next={path}&user_initiated=true".format(path=path)
