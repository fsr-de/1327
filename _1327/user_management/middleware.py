from ipaddress import ip_address, ip_network
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.shortcuts import resolve_url


class IPRangeUserMiddleware:

	def __init__(self, get_response):
		self.get_response = get_response
		try:
			self.ip_ranges = {ip_network(k): v for k, v in settings.ANONYMOUS_IP_RANGE_GROUPS.items()}
		except ValueError as e:
			raise ImproperlyConfigured from e

	def __call__(self, request):
		self.process_request(request)
		response = self.get_response(request)
		return response

	def process_request(self, request):
		if request.user.is_anonymous:
			address = ip_address(request.META.get('REMOTE_ADDR'))
			for ip_range, group_name in self.ip_ranges.items():
				if address in ip_range:
					# user is in this IP range
					request.user._ip_range_group_name = group_name
					break


class LoginRedirectMiddleware:
	def __init__(self, get_response):
		self.get_response = get_response

	def __call__(self, request):
		response = self.get_response(request)
		return response

	def process_exception(self, request, exception):
		if isinstance(exception, PermissionDenied) and not request.user.is_authenticated and not request.is_ajax():
			path = request.build_absolute_uri()
			resolved_login_url = resolve_url(settings.LOGIN_URL)
			# If the login url is the same scheme and net location then just
			# use the path as the "next" url.
			login_scheme, login_netloc = urlparse(resolved_login_url)[:2]
			current_scheme, current_netloc = urlparse(path)[:2]

			if (
				(not login_scheme or login_scheme == current_scheme) and
				(not login_netloc or login_netloc == current_netloc)
			):
				path = request.get_full_path()

			from django.contrib.auth.views import redirect_to_login
			return redirect_to_login(
				path,
				resolved_login_url,
				REDIRECT_FIELD_NAME,
			)
