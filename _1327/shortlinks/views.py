from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, Http404, redirect, render
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from _1327.shortlinks.utils import get_document_selection
from .forms import ShortlinkForm
from .models import Shortlink


def shortlinks_index(request):
	if not request.user.is_superuser:
		raise PermissionDenied

	return render(request, 'shortlinks_index.html', {
		'shortlinks': Shortlink.objects.all(),
	})


def shortlink_create(request):
	if not request.user.is_superuser:
		raise PermissionDenied

	form = ShortlinkForm(request.POST or None, instance=Shortlink())

	if form.is_valid():
		form.save()
		messages.success(request, _("Successfully created shortlink."))
		return redirect('shortlinks_index')
	else:
		return render(
			request,
			'shortlink_edit.html',
			{
				'form': form,
				'document_selection': get_document_selection(request),
			}
		)


def shortlink_delete(request):
	if not request.user.is_superuser:
		raise PermissionDenied

	if request.is_ajax() and request.method == "POST":
		shortlink = Shortlink.objects.get(id=request.POST['id'])
		shortlink.delete()
		messages.success(request, _("Successfully deleted Shortlink."))
		return HttpResponse()
	raise Http404()


def view(request, title):
	shortlink = get_object_or_404(Shortlink, url_title=title)
	shortlink.visit_count += 1
	shortlink.last_access = timezone.now()
	shortlink.save()
	if shortlink.link:
		return redirect(shortlink.link)
	elif shortlink.document:
		return redirect(shortlink.document.get_view_url_name(), title=shortlink.document.url_title)


def edit(request, title):
	if not request.user.is_superuser:
		raise PermissionDenied

	shortlink = get_object_or_404(Shortlink, url_title=title)
	form = ShortlinkForm(request.POST or None, instance=shortlink)

	if form.is_valid():
		form.save()
		messages.success(request, _("Successfully edited shortlink."))
		return redirect('shortlinks_index')
	else:
		return render(
			request,
			'shortlink_edit.html',
			{
				'form': form,
				'document_selection': get_document_selection(request),
			}
		)
