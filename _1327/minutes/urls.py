from django.conf.urls import url
from django.contrib import admin

from _1327.documents import urls as document_urls
from _1327.documents import views as documents_views
from . import views

admin.autodiscover()

urlpatterns = [
	url(r"(?P<groupid>[\d]+)$", views.list, name='list'),
	url(r"(?P<title>[\w-]+)/view$", documents_views.view, name='view'),
]
urlpatterns.extend(document_urls.document_urlpatterns)
