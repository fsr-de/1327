from django.conf.urls import url

from . import views

app_name = 'information_pages'

urlpatterns = [
	url(r"unlinked$", views.unlinked_list, name='unlinked_list'),
]
