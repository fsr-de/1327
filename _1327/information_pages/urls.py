from django.urls import path

from . import views

app_name = "information_pages"

urlpatterns = [
	path("unlinked", views.unlinked_list, name="unlinked_list"),
]
