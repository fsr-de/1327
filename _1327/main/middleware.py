from django.http import HttpResponsePermanentRedirect

EXCLUDED_URLS = ['admin', 'hijack']


class RedirectToNoSlash:

	def process_request(self, request):
		if all(['/' + path not in request.path for path in EXCLUDED_URLS]) and request.path != '/':
			if request.path[-1] == '/':
				return HttpResponsePermanentRedirect(request.path[:-1])
