from django.urls import path

from . import views


app_name = "emails"

urlpatterns = [
	path("", views.emails_index, name="index"),
	path("/search", views.emails_search, name="search"),
	path("/<int:year>/<int:month>", views.emails_archive, name="archive"),
	path("/view/<int:email_id>", views.emails_view, name="view"),
	path("/download/<int:email_id>", views.emails_download, name="download"),
	path("/download-attachment/<int:email_id>/<int:attachment_index>", views.emails_download_attachment, name="download_attachment"),
]
