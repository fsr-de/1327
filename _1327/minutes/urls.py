from django.conf.urls import url

from _1327.documents import urls as document_urls
from _1327.documents import views as document_views
from . import views

app_name = 'minutes'

urlpatterns = [
	url(r"list/(?P<groupid>[\d]+)$", views.list, name='list'),
	url(r"(?P<title>[\w\-/]+)/edit$", document_views.edit, name='edit'),
]
urlpatterns.extend(document_urls.document_urlpatterns)
urlpatterns.extend([
	url(r"(?P<title>[\w\-/]+)$", document_views.view, name='view'),
])
