from django.contrib.auth.mixins import AccessMixin
from django.http import Http404

from _1327.tenca_django.connection import connection


class TencaSingleListMixin:
	def setup(self, request, *args, **kwargs):
		super().setup(request, *args, **kwargs)
		self.mailing_list = connection.get_list(kwargs["list_id"])
		if not self.mailing_list:
			raise Http404


class TencaListAdminMixin(AccessMixin, TencaSingleListMixin):
	def dispatch(self, request, *args, **kwargs):
		if not (request.user.is_staff or self.mailing_list.is_owner(request.user.email)):
			return self.handle_no_permission()
		return super().dispatch(request, *args, **kwargs)
