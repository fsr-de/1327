from django.urls import path

from _1327.tenca_django import views

app_name = "tenca_django"

urlpatterns = [
	path("index", views.TencaDashboard.as_view(), name="tenca_dashboard"),
	path("<str:hash_id>", views.TencaSubscriptionView.as_view(), name="tenca_manage_subscription"),
	path("manage/<str:list_id>", views.TencaListAdminView.as_view(), name="tenca_manage_list"),
	path("manage/<str:list_id>/<str:email>", views.TencaMemberEditView.as_view(), name="tenca_edit_member"),
]
