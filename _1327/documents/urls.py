from django.urls import path, register_converter

from _1327.main.utils import SlugWithSlashConverter
from . import views

app_name = "documents"

register_converter(SlugWithSlashConverter, 'slugwithslash')


urlpatterns = [
	path("revert", views.revert, name="revert"),
	path("search", views.search, name="search"),
	path("preview", views.preview, name="preview"),
	path("attachment/create", views.create_attachment, name="create_attachment"),
	path("attachment/delete", views.delete_attachment, name="delete_attachment"),
	path("attachment/download", views.download_attachment, name="download_attachment"),
	path("attachment/update", views.update_attachment_order, name="update_attachment_order"),
	path("attachment/<int:document_id>/get", views.get_attachments, name="get_attachments"),
	path("attachment/change", views.change_attachment, name="change_attachment"),

	path("<slug:document_type>/create", views.create, name="create"),

	path("<slugwithslash:title>/autosave", views.autosave, name="autosave"),
	path("<slugwithslash:title>/autosave/delete", views.delete_autosave, name="delete_autosave"),
	path("<slugwithslash:title>/publish/<int:next_state_id>", views.publish, name="publish"),
	path("<slugwithslash:title>/render", views.render_text, name="render"),
	path("<slugwithslash:title>/delete-cascade", views.get_delete_cascade, name="get_delete_cascade"),
	path("<slugwithslash:title>/delete", views.delete_document, name="delete_document"),
]

document_urlpatterns = [
	path("<slugwithslash:title>/versions", views.versions, name="versions"),
	path("<slugwithslash:title>/permissions", views.permissions, name="permissions"),
	path("<slugwithslash:title>/attachments", views.attachments, name="attachments"),
]
