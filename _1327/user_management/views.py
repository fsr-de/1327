from django.conf import settings
from django.contrib.auth import logout as auth_logout
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render

from .forms import UserImpersonationForm


def logout(request):
	auth_logout(request)
	return redirect(settings.LOGOUT_REDIRECT_URL)


def view_as(request):
	if not request.user.is_superuser:
		raise PermissionDenied

	form = UserImpersonationForm()
	return render(request, "user_impersonation.html", {
		'form': form,
	})
