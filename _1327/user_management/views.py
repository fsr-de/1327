from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render, get_object_or_404
from django.utils.translation import ugettext_lazy as _

from .forms import UserImpersonationForm, GroupEdit


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


def edit_group(request, group_id):
	group = get_object_or_404(Group, id=group_id)
	form = GroupEdit(request.POST or None, instance=group, initial={
		'add_information_document': group.permissions.filter(codename="add_informationdocument").exists(),
		'add_minutes': group.permissions.filter(codename="add_minutesdocument").exists(),
		'add_poll': group.permissions.filter(codename="add_poll").exists(),
		'users': group.user_set.all()
	})

	print(form.fields)
	#print(form.fields["users"].is_valid())
	if form.is_valid():
		form.save()
		messages.success(request, _("Successfully edited group."))
		return redirect('home')
	else:
		return render(request, "edit_group.html", {
			'form': form,
			'group': group
		})
