from django.urls import path
from _1327.tenca_django import views

app_name = "tenca_django"

urlpatterns = [
	path("dashboard", views.TencaDashboard.as_view(), name="tenca_dashboard"),
	path("<str:hash_id>", views.TencaSubscriptionView.as_view(), name="tenca_manage_subscription"),
	path("confirm/<str:list_id>/<str:token>", views.TencaActionConfirmView.as_view(), name="confirm"),
	path("report/<str:list_id>/<str:token>", views.TencaReportView.as_view(), name="report"),
	path("manage/<str:list_id>", views.TencaListAdminView.as_view(), name="tenca_manage_list"),
	path("manage/<str:list_id>/member", views.TencaMemberEditView.as_view(), name="tenca_edit_member"),
	path("manage/<str:list_id>/delete", views.TencaListDeleteView.as_view(), name="tenca_delete_list"),
]
