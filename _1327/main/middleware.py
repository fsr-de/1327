from django.http import HttpResponsePermanentRedirect

EXCLUDED_URLS = ['admin', 'hijack']


class RedirectToNoSlash:

	def __init__(self, get_response):
		self.get_response = get_response

	def __call__(self, request):
		if all(['/' + path not in request.path for path in EXCLUDED_URLS]) and request.path != '/':
			if request.path[-1] == '/':
				return HttpResponsePermanentRedirect(request.path[:-1])

		response = self.get_response(request)
		return response
