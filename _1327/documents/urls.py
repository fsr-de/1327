from django.conf.urls import patterns, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('_1327.documents.views',
	url(r"revert/$", 'revert', name='revert'),
)
