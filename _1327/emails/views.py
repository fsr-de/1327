from datetime import datetime

from django.db.models import Count, Max, Q
from django.db.models.functions import TruncMonth, TruncYear
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from sendfile import sendfile

from _1327.emails.forms import QuickSearchForm, SearchForm
from _1327.emails.models import Email
import _1327.emails.utils as utils


def emails_index(request):
	result = Email.objects.aggregate(Max('date'))
	date = datetime.now() if result['date__max'] is None else result['date__max']
	return redirect('emails:archive', date.year, date.month)


def emails_archive(request, year, month):
	emails = Email.objects.filter(
		date__year__exact=year,
		date__month__exact=month
	).order_by(f"-{Email.objects.tree_id_attr}", Email.objects.left_attr)

	current_month = datetime(year, month, 1)
	next_month = datetime(year if month < 12 else year + 1, month + 1 if month < 12 else 1, 1)
	previous_month = datetime(year if month > 1 else year - 1, month - 1 if month > 1 else 12, 1)

	statistics = Email.objects\
		.annotate(year=TruncYear('date'), month=TruncMonth('date'))\
		.values('year', 'month')\
		.annotate(count=Count('*'))\
		.order_by('-year', '-month')

	return render(request, "emails_archive.html", {
		'emails': emails,
		'current_month': current_month,
		'next_month': next_month,
		'previous_month': previous_month,
		'search_form': QuickSearchForm(),
		'statistics': statistics
	})


def emails_search(request):
	form = SearchForm(request.GET)
	if form.is_valid():
		text = form.cleaned_data['text']
		sender = form.cleaned_data['sender']
		receiver = form.cleaned_data['receiver']
		received_after = form.cleaned_data['received_after']
		received_before = form.cleaned_data['received_before']
		has_attachments = form.cleaned_data['has_attachments']

		emails = Email.objects.all()

		if len(text) > 0:
			emails = emails.filter(Q(subject__icontains=text) | Q(text__icontains=text))
		if len(sender) > 0:
			emails = emails.filter(Q(from_name__icontains=sender) | Q(from_address__icontains=sender))
		if len(receiver) > 0:
			emails = emails.filter(
				Q(to_names__icontains=receiver) | Q(to_addresses__icontains=receiver) |
				Q(cc_names__icontains=receiver) | Q(cc_addresses__icontains=receiver)
			)
		if received_after is not None:
			emails = emails.filter(date__gte=received_after)
		if received_before is not None:
			emails = emails.filter(date__lte=received_before)
		if has_attachments:
			emails = emails.filter(num_attachments__gt=0)

		emails = emails.order_by(f"-{Email.objects.tree_id_attr}", Email.objects.left_attr)
	else:
		emails = []

	return render(request, "emails_search.html", {
		'emails': emails,
		'search_form': form
	})


def emails_view(request, email_id):
	email_entity = get_object_or_404(Email, id=email_id)
	message = utils.get_message_for_email_entity(email_entity)
	content = utils.get_content_as_safe_html(message)

	return render(request, "emails_view.html", {
		'email': email_entity,
		'emails': email_entity.get_family,
		'content': content,
		'attachment_info': utils.get_attachment_info(message)
	})


def emails_download(request, email_id):
	email_entity = get_object_or_404(Email, id=email_id)
	return sendfile(request, email_entity.envelope.path, attachment=True, attachment_filename=email_entity.envelope.name)


def emails_download_attachment(request, email_id, attachment_index):
	email_entity = get_object_or_404(Email, id=email_id)
	message = utils.get_message_for_email_entity(email_entity)

	content, content_type, filename = utils.get_attachment(message, attachment_index)

	# TODO: Use as_attachment and filename parameters once we use Django 2.1
	# https://docs.djangoproject.com/en/2.1/ref/request-response/#fileresponse-objects
	response = HttpResponse(content, content_type=content_type)
	response['Content-Disposition'] = f'inline; filename="{filename}"'
	return response
