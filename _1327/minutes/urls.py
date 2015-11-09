from django.conf.urls import patterns, url
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('_1327.minutes.views',
	url(r"^$", 'list', name='list'),
	url(r"create$", 'create', name='create'),
	url(r"(?P<title>[\w-]+)/edit$", 'edit', name='edit'),
	url(r"(?P<title>[\w-]+)/autosave$", 'autosave', name='autosave'),
	url(r"(?P<title>[\w-]+)/versions$", 'versions', name="versions"),
	url(r"(?P<title>[\w-]+)/permissions$", 'permissions', name="permissions"),
	url(r"(?P<title>[\w-]+)/attachments$", 'attachments', name="attachments"),
	url(r"(?P<title>[\w-]+)$", 'view', name='view'),
)
