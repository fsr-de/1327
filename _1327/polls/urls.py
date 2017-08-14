from django.conf.urls import url

from _1327.documents import urls as document_urls
from _1327.documents import views as document_views
from . import views

app_name = 'polls'

urlpatterns = [
	url(r"list$", views.index, name="index"),
	url(r"(?P<title>[\w\-/]+)/edit$", document_views.edit, name='edit'),
	url(r"(?P<title>[\w\-/]+)/admin-result$", views.results_for_admin, name='results_for_admin'),
]
urlpatterns.extend(document_urls.document_urlpatterns)
urlpatterns.extend([
	url(r"(?P<title>[\w\-/]+)$", document_views.view, name='view'),
])
