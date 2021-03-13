from django.urls import path

from _1327.tenca_django import views

app_name = "tenca_django"

urlpatterns = [
	path("confirm/<str:list_id>/<str:token>", views.confirm, name="confirm"),
	path("index", views.TencaDashboard.as_view(), name="tenca_dashboard"),
	path("report/<str:list_id>/<str:token>", views.report, name="report"),
]
