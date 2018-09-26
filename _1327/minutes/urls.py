from django.urls import path, register_converter

from _1327.documents import urls as document_urls
from _1327.documents import views as document_views
from _1327.main.utils import SlugWithSlashConverter
from . import views

app_name = "minutes"

register_converter(SlugWithSlashConverter, 'slugwithslash')

urlpatterns = [
	path("list/<int:groupid>", views.list, name="list"),
	path("<slugwithslash:title>/edit", document_views.edit, name="edit"),
	path("search/<int:groupid>", views.search, name="search"),
]
urlpatterns.extend(document_urls.document_urlpatterns)
urlpatterns.extend([
	path("<slugwithslash:title>", document_views.view, name="view"),
])
