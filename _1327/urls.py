from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('_1327',
	url(r"^$", 'main.views.index'),
	url(r"^documents/", include('_1327.documents.urls', namespace='documents')),
	url(r"^information/", include('_1327.information_pages.urls', namespace='information_pages')),
	url(r"^login$", 'main.views.login'),
	url(r"^logout$", 'main.views.logout'),
	url(r'^page_admin/', include('_1327.page_admin.urls')),

	url(r'^admin/', include(admin.site.urls)),
)
