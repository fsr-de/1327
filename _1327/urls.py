from django.conf.urls import include, patterns, url
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('_1327',  # noqa
	url(r"^$", 'main.views.index', name='index'),
	url(r"^documents/", include('_1327.documents.urls', namespace='documents')),
	url(r"^minutes/", include('_1327.minutes.urls', namespace='minutes')),
	url(r"^login$", 'user_management.views.login', name='login'),
	url(r"^logout$", 'user_management.views.logout', name='logout'),
	url(r'^polls/', include('_1327.polls.urls', namespace='polls')),

	url(r'^menu_items$', 'main.views.menu_items_index', name='menu_items_index'),
	url(r"^menu_item/create$", 'main.views.menu_item_create', name="menu_item_create"),
	url(r"^menu_item/(\d+)/edit$", 'main.views.menu_item_edit', name="menu_item_edit"),
	url(r"^menu_item_delete$", 'main.views.menu_item_delete', name="menu_item_delete"),
	url(r"^menu_item/update_order$", 'main.views.menu_items_update_order', name="menu_items_update_order"),

	url(r'^admin/', include(admin.site.urls)),
)
