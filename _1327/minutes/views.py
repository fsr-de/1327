import re

from django.shortcuts import redirect, render
from django.utils.html import escape
from django.utils.safestring import mark_safe

from _1327.documents.utils import get_permitted_documents
from _1327.minutes.forms import SearchForm
from _1327.minutes.models import MinutesDocument


def search(request, groupid):
	if request.method == 'POST':
		form = SearchForm(request.POST)
		if form.is_valid():
			search_text = form.cleaned_data['search_phrase']
	else:
		# redirect to minutes list
		return redirect("minutes:list", groupid=groupid)

	# filter for documents that contain the searched for string
	minutes = MinutesDocument.objects.filter(text__icontains=search_text).prefetch_related('labels').order_by('-date')

	# only show permitted documents
	minutes, own_group = get_permitted_documents(minutes, request, groupid)

	# find lines containing the searched for string
	result = {}
	for m in minutes:
		# find lines with the searched for string and mark it as bold
		lines = m.text.splitlines()
		lines = [
			mark_safe(
				re.sub(
					r'(' + re.escape(escape(search_text)) + ')',
					r'<b>\1</b>', escape(line),
					flags=re.IGNORECASE
				)
			)
			for line in lines if (line.casefold().find(search_text.casefold()) != -1)
		]

		if m.date.year not in result:
			result[m.date.year] = []

		result[m.date.year].append((m, lines))

	return render(request, "minutes_with_lines_list.html", {
		'minutes_list': sorted(result.items(), reverse=True),
		'own_group': own_group,
		'group_id': groupid,
		'search_form': SearchForm(),
		'phrase': search_text,
	})


def list(request, groupid):
	minutes = MinutesDocument.objects.all().prefetch_related('labels').order_by('-date')
	minutes, own_group = get_permitted_documents(minutes, request, groupid)

	result = {}
	for m in minutes:
		if m.date.year not in result:
			result[m.date.year] = []
		result[m.date.year].append((m, []))
	return render(request, "minutes_list.html", {
		'minutes_list': sorted(result.items(), reverse=True),
		'own_group': own_group,
		'group_id': groupid,
		'search_form': SearchForm(),
	})
