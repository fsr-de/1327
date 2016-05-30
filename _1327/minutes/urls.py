from django.conf.urls import patterns, url
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('_1327.minutes.views',  # noqa
	url(r"^$", 'list', name='list'),
	url(r"(?P<groupid>[\d]+)$", 'list', name='list'),
)
