from django.conf import settings
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, render

from .forms import LoginForm, UserImpersonationForm


def login(request):
	if request.method == 'POST':
		form = LoginForm(request.POST)
		if form.is_valid():
			auth_login(request, form.get_user())
			return redirect(settings.LOGIN_REDIRECT_URL)
	else:
		form = LoginForm()

	return render(request, "login.html", {
		'form': form
	})


def logout(request):
	auth_logout(request)
	return redirect(settings.LOGOUT_REDIRECT_URL)


def view_as(request):
	if not request.user.is_superuser:
		raise PermissionDenied

	if request.method == 'POST':
		form = UserImpersonationForm(request.POST)
		if form.is_valid():
			return redirect(reverse('login_with_id', args=[form.cleaned_data['username'].id]))
	else:
		form = UserImpersonationForm()

	return render(request, "user_impersonation.html", {
		'form': form,
	})
