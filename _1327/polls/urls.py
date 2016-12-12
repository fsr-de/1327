from django.conf.urls import url

from _1327.documents import urls as document_urls
from . import views

urlpatterns = [
	url(r"^$", views.index, name="index"),
]
urlpatterns.extend(document_urls.urlpatterns)
