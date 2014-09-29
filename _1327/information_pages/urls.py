from django.conf.urls import patterns, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('_1327.information_pages.views',
	url(r"edit/(?P<title>[\w-]+)/$", 'edit', name='edit'),
	url(r"versions/(?P<title>[\w-]+)/$", 'versions', name="versions"),
	url(r"(?P<title>[\w-]+)/$", 'view_information', name='view_information'),
)
