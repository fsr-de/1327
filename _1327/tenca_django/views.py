from tenca import connection
from django.views.generic import TemplateView

connection = connection.Connection()

class TencaDashboard(TemplateView):
	template_name = "tenca_django/dashboard.html"
