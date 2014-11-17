from django.shortcuts import render
from _1327.user_management.decorators import admin_required

@admin_required
def index(request):
	return render(request, "admin_index.html")
