from django.conf.urls import patterns, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('_1327.documents.views',
	url(r"revert/$", 'revert', name='revert'),
	url(r"deleteattachment/$", 'delete_attachment', name='delete_attachment'),
	url(r"download/$", 'download_attachment', name='download_attachment'),
)
