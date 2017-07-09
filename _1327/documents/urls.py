from django.conf.urls import url

from . import views

app_name = 'documents'

urlpatterns = [
	url(r"revert$", views.revert, name='revert'),
	url(r"search$", views.search, name='search'),
	url(r"preview$", views.preview, name='preview'),
	url(r"attachment/create$", views.create_attachment, name='create_attachment'),
	url(r"attachment/delete$", views.delete_attachment, name='delete_attachment'),
	url(r"attachment/download$", views.download_attachment, name='download_attachment'),
	url(r"attachment/update$", views.update_attachment_order, name="update_attachment_order"),
	url(r"attachment/(?P<document_id>[\d]+)/get$", views.get_attachments, name='get_attachments'),
	url(r"attachment/change", views.change_attachment, name='change_attachment'),

	url(r"(?P<document_type>[\w-]+)/create$", views.create, name='create'),

	url(r"(?P<title>[\w\-/]+)/autosave$", views.autosave, name='autosave'),
	url(r"(?P<title>[\w\-/]+)/publish/(?P<state_id>[\d]+)$", views.publish, name='publish'),
	url(r"(?P<title>[\w\-/]+)/render$", views.render_text, name="render"),
	url(r"(?P<title>[\w\-/]+)/delete-cascade$", views.get_delete_cascade, name="get_delete_cascade"),
	url(r"(?P<title>[\w\-/]+)/delete$", views.delete_document, name="delete_document"),
]

document_urlpatterns = [
	url(r"(?P<title>[\w\-/]+)/versions$", views.versions, name="versions"),
	url(r"(?P<title>[\w\-/]+)/permissions$", views.permissions, name="permissions"),
	url(r"(?P<title>[\w\-/]+)/attachments$", views.attachments, name="attachments"),
]
