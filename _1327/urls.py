from django.conf.urls import patterns, include, url
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('_1327',
	url(r"^$", 'main.views.index'),
	url(r"^documents/", include('_1327.documents.urls', namespace='documents')),
	url(r"^minutes/", include('_1327.minutes.urls', namespace='minutes')),
	url(r"^login$", 'user_management.views.login'),
	url(r"^logout$", 'user_management.views.logout'),
	url(r'^polls/', include('_1327.polls.urls', namespace='polls')),

	url(r'^admin/', include(admin.site.urls)),
	url(r"^", include('_1327.information_pages.urls', namespace='information_pages')),
)
