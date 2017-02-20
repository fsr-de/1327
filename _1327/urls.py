from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth import views as auth_views

from _1327.documents import urls as document_urls
from _1327.main import views as main_views
from _1327.shortlinks import views as shortlinks_views
from _1327.user_management import views as user_management_views

admin.autodiscover()

urlpatterns = [
	url(r"^$", main_views.index, name='index'),
	url(r"^" + settings.MINUTES_URL_NAME + "/", include('_1327.minutes.urls', namespace='minutes')),
	url(r"^" + settings.POLLS_URL_NAME + "/", include('_1327.polls.urls', namespace='polls')),
	url(r"^documents/", include('_1327.documents.urls', namespace='documents')),
	url(r"^information_pages/", include('_1327.information_pages.urls', namespace='information_pages')),
	url(r"^login$", auth_views.login, {'template_name': 'login.html', }, name='login'),
	url(r"^logout$", user_management_views.logout, name='logout'),
	url(r'^view_as$', user_management_views.view_as, name='view_as'),

	url(r'^abbreviation_explanation/', main_views.abbreviation_explanation_edit, name="abbreviation_explanation"),

	url(r'^menu_items$', main_views.menu_items_index, name='menu_items_index'),
	url(r"^menu_item/create$", main_views.menu_item_create, name="menu_item_create"),
	url(r"^menu_item/(\d+)/edit$", main_views.menu_item_edit, name="menu_item_edit"),
	url(r"^menu_item_delete$", main_views.menu_item_delete, name="menu_item_delete"),
	url(r"^menu_item/update_order$", main_views.menu_items_update_order, name="menu_items_update_order"),

	url(r'^shortlinks$', shortlinks_views.shortlinks_index, name='shortlinks_index'),
	url(r'^shortlink/create$', shortlinks_views.shortlink_create, name='shortlink_create'),
	url(r'^shortlink/delete$', shortlinks_views.shortlink_delete, name='shortlink_delete'),

	url(r'^admin/', include(admin.site.urls)),
	url(r'^hijack/', include('hijack.urls')),
]
urlpatterns.extend(document_urls.document_urlpatterns)

custom_urlpatterns = [
	url(r"(?P<title>[\w\-/]+)/edit$", main_views.edit, name='edit'),
	url(r"(?P<title>[\w\-/]+)$", main_views.view, name='view'),
]
urlpatterns.extend(custom_urlpatterns)
