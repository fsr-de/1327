from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('_1327',
	url(r"^$", 'main.views.index'),
	url(r"^login$", 'auth.views.login'),
	url(r"^logout$", 'auth.views.logout'),

	url(r'^admin/', include(admin.site.urls)),
)
