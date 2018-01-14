from django.urls import path, register_converter

from _1327.documents import urls as document_urls
from _1327.documents import views as document_views
from _1327.main.utils import SlugWithSlashConverter
from . import views

app_name = "polls"

register_converter(SlugWithSlashConverter, 'slugwithslash')

urlpatterns = [
	path("list", views.index, name="index"),
	path("<slugwithslash:title>/edit", document_views.edit, name="edit"),
	path("<slugwithslash:title>/admin-result", views.results_for_admin, name="results_for_admin"),
]
urlpatterns.extend(document_urls.document_urlpatterns)
urlpatterns.extend([
	path("<slugwithslash:title>", document_views.view, name="view"),
])
