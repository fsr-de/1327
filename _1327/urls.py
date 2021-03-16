from django.conf import settings
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path, register_converter
from django.utils.module_loading import import_string

from mozilla_django_oidc import views as oidc_views
from mozilla_django_oidc.utils import import_from_settings

from _1327.documents import urls as document_urls
from _1327.main import views as main_views
from _1327.main.utils import SlugWithSlashConverter
from _1327.shortlinks import views as shortlinks_views
from _1327.user_management import views as user_management_views
from _1327.user_management.forms import LoginUsernameForm

urlpatterns = [
	path("", main_views.index, name="index"),
	path("" + settings.MINUTES_URL_NAME + "/", include("_1327.minutes.urls")),
	path("" + settings.POLLS_URL_NAME + "/", include("_1327.polls.urls")),
	path("documents/", include("_1327.documents.urls")),
	path("information_pages/", include("_1327.information_pages.urls")),
	path("login", auth_views.LoginView.as_view(
		template_name="login.html",
		authentication_form=LoginUsernameForm,
		redirect_authenticated_user=True,
		extra_context={"openid_login": settings.ACTIVATE_OPEN_ID_LOGIN},
	), name="login"),
	path("logout", user_management_views.logout, name="logout"),
	path("view_as", user_management_views.view_as, name="view_as"),

	path("abbreviation_explanation", main_views.abbreviation_explanation_edit, name="abbreviation_explanation"),

	path("menu_items", main_views.menu_items_index, name="menu_items_index"),
	path("menu_item/create", main_views.menu_item_create, name="menu_item_create"),
	path("menu_item/<int:menu_item_pk>/edit", main_views.menu_item_edit, name="menu_item_edit"),
	path("menu_item_delete", main_views.menu_item_delete, name="menu_item_delete"),
	path("menu_item/update_order", main_views.menu_items_update_order, name="menu_items_update_order"),

	path("set_lang", main_views.set_lang, name="set_lang"),

	path("shortlinks", shortlinks_views.shortlinks_index, name="shortlinks_index"),
	path("shortlink/create", shortlinks_views.shortlink_create, name="shortlink_create"),
	path("shortlink/delete", shortlinks_views.shortlink_delete, name="shortlink_delete"),

	path("admin/", admin.site.urls),
	path("hijack/", include("hijack.urls")),
]

# see https://mozilla-django-oidc.readthedocs.io/en/stable/installation.html#add-routing-to-urls-py for documented import
# this is done manually here because of problems with trailing slashes
OIDCCallbackClass = import_string(import_from_settings('OIDC_CALLBACK_CLASS', 'mozilla_django_oidc.views.OIDCAuthenticationCallbackView'))
OIDCAuthenticateClass = import_string(import_from_settings('OIDC_AUTHENTICATE_CLASS', 'mozilla_django_oidc.views.OIDCAuthenticationRequestView'))
urlpatterns.extend([
	path('oidc/callback', OIDCCallbackClass.as_view(), name='oidc_authentication_callback'),
	path('oidc/authenticate', OIDCAuthenticateClass.as_view(), name='oidc_authentication_init'),
	path('oidc/logout', oidc_views.OIDCLogoutView.as_view(), name='oidc_logout'),
])

urlpatterns.extend(document_urls.document_urlpatterns)

register_converter(SlugWithSlashConverter, 'slugwithslash')

custom_urlpatterns = [
	path("<slugwithslash:title>/edit", main_views.edit, name="edit"),
	path("<slugwithslash:title>", main_views.view, name="view"),
]
urlpatterns.extend(custom_urlpatterns)


if settings.ENABLE_DEBUG_TOOLBAR:
	import debug_toolbar
	urlpatterns = [path('__debug__/', include(debug_toolbar.urls))] + urlpatterns

if settings.ENABLE_MAILING_LISTS:
	urlpatterns = [path("lists/", include("_1327.tenca_django.urls"))] + urlpatterns
