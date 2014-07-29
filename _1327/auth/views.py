from django.conf import settings
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils.translation import ugettext_lazy as _
from _1327.auth.forms import LoginForm

def login(request):
	if request.method == 'POST':
		form = LoginForm(request.POST)
		if form.is_valid():
			auth_login(request, form.get_user())
			messages.success(request, _("You have been successfully logged in."))
			return redirect(settings.LOGIN_REDIRECT_URL)
	else:
		form = LoginForm()

	return render(request, "login.html", {
		'form': form
	})

def logout(request):
	auth_logout(request)
	messages.success(request, _("You have been successfully logged out."))
	return redirect(settings.LOGOUT_REDIRECT_URL)
