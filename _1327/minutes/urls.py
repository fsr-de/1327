from django.conf.urls import url
from django.contrib import admin

from _1327.documents import urls as document_urls
from . import views

admin.autodiscover()

urlpatterns = [
	url(r"list/(?P<groupid>[\d]+)$", views.list, name='list'),
]
urlpatterns.extend(document_urls.document_urlpatterns)
