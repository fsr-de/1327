from django.conf.urls import patterns, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('_1327.information_pages.views',
	url(r"edit/(?P<title>[\w-]+)/$", 'edit', name='edit'),
	url(r"(?P<title>[\w-]+)/$", 'view_information', name='view_information'),
)
