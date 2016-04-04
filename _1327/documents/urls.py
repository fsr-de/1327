from django.conf.urls import patterns, url
from django.contrib import admin

admin.autodiscover()


urlpatterns = patterns('_1327.documents.views',  # noqa
	url(r"revert$", 'revert', name='revert'),
	url(r"search$", 'search', name='search'),
	url(r"attachment/create$", 'create_attachment', name='create_attachment'),
	url(r"attachment/delete$", 'delete_attachment', name='delete_attachment'),
	url(r"attachment/download$", 'download_attachment', name='download_attachment'),
	url(r"attachment/update$", 'update_attachment_order', name="update_attachment_order"),
	url(r"attachment/(?P<document_id>[\d]+)/get$", 'get_attachments', name='get_attachments'),
	url(r"attachment/no-direct-download", 'change_attachment_no_direct_download', name='change_attachment_no_direct_download'),

	url(r"(?P<document_type>[\w-]+)/create$", 'create', name='create'),
	url(r"(?P<title>[\w-]+)/edit$", 'edit', name='edit'),
	url(r"(?P<title>[\w-]+)/autosave$", 'autosave', name='autosave'),
	url(r"(?P<title>[\w-]+)/versions$", 'versions', name="versions"),
	url(r"(?P<title>[\w-]+)/permissions$", 'permissions', name="permissions"),
	url(r"(?P<title>[\w-]+)/attachments$", 'attachments', name="attachments"),
	url(r"(?P<title>[\w-]+)$", 'view', name='view'),
)
