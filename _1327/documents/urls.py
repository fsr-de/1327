from django.conf.urls import patterns, url
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('_1327.documents.views',  # noqa
	url(r"revert$", 'revert', name='revert'),
	url(r"attachment/delete$", 'delete_attachment', name='delete_attachment'),
	url(r"attachment/download$", 'download_attachment', name='download_attachment'),
	url(r"attachment/update$", 'update_attachment_order', name="update_attachment_order"),
	url(r"attachment/(?P<document_id>[\d]+)/get$", 'get_attachments', name='get_attachments'),
	url(r"attachment/no-direct-download", 'change_attachment_no_direct_download', name='change_attachment_no_direct_download'),
)
