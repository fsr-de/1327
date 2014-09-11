from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('_1327',
	url(r"^$", 'main.views.index'),
	url(r"^login$", 'main.views.login'),
	url(r"^logout$", 'main.views.logout'),

	url(r'^admin/', include(admin.site.urls)),
)
