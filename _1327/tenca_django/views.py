from django.views.generic import TemplateView


class TencaDashboard(TemplateView):
	template_name = "tenca_django/dashboard.html"
