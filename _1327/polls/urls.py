from django.conf.urls import url

from _1327.documents import urls as document_urls
from . import views

urlpatterns = [
	url(r"^$", views.index, name="index"),
	url(r"(?P<title>[\w-]+)/view$", views.view, name='view'),
]
urlpatterns.extend(document_urls.document_urlpatterns)
