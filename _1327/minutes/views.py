import re

from django.contrib.auth.models import Group
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.shortcuts import Http404, redirect, render
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.translation import get_language
from guardian.core import ObjectPermissionChecker

from _1327.minutes.forms import SearchForm
from _1327.minutes.models import MinutesDocument


def get_permitted_minutes(minutes, request, groupid):
	groupid = int(groupid)
	try:
		group = Group.objects.get(id=groupid)
	except ObjectDoesNotExist:
		raise Http404

	own_group = request.user.is_superuser or group in request.user.groups.all()

	# Prefetch group permissions
	group_checker = ObjectPermissionChecker(group)
	group_checker.prefetch_perms(minutes)

	# Prefetch user permissions
	user_checker = ObjectPermissionChecker(request.user)
	user_checker.prefetch_perms(minutes)

	# Prefetch ip group permissions
	ip_range_group_name = request.user._ip_range_group_name if hasattr(request.user, '_ip_range_group_name') else None
	if ip_range_group_name:
		ip_range_group = Group.objects.get(name=ip_range_group_name)
		ip_range_group_checker = ObjectPermissionChecker(ip_range_group)

	permitted_minutes = []
	for m in minutes:
		# we show all documents for which the requested group has edit permissions
		# e.g. if you request FSR minutes, all minutes for which the FSR group has edit rights will be shown
		if not group_checker.has_perm(m.edit_permission_name, m):
			continue
		# we only show documents for which the user has view permissions
		if not user_checker.has_perm(MinutesDocument.get_view_permission(), m) and (not ip_range_group_name or not ip_range_group_checker.has_perm(MinutesDocument.get_view_permission(), m)):
			continue
		permitted_minutes.append(m)

	return permitted_minutes, own_group


def search(request, groupid):
	if request.method == 'POST':
		form = SearchForm(request.POST)
		if form.is_valid():
			search_text = form.cleaned_data['search_phrase']
	else:
		# redirect to minutes list
		return redirect("minutes:list", groupid=groupid)

	# filter for documents that contain the searched for string
	minutes = MinutesDocument.objects.filter(Q(text_de__icontains=search_text) | Q(text_en__icontains=search_text)).prefetch_related('labels').order_by('-date')

	# only show permitted documents
	minutes, own_group = get_permitted_minutes(minutes, request, groupid)

	# find lines containing the searched for string
	result = {}
	for m in minutes:
		# find lines with the searched for string and mark it as bold
		lines = []
		for language in ['de', 'en']:
			lines_lang = getattr(m, 'text_' + language).splitlines()

			lines_lang = [
				mark_safe(
					re.sub(
						r'(' + re.escape(escape(search_text)) + ')',
						r'<b>\1</b>', escape(line),
						flags=re.IGNORECASE
					)
				)
				for line in lines_lang if (line.casefold().find(search_text.casefold()) != -1)
			]

			# We're searching the string on all possible languages but if there's a match in a different language
			# than the one selected it is highlighted in italics.
			if not get_language().startswith(language):
				lines_lang = [mark_safe('<i>' + line + '</i>') for line in lines_lang]

			lines += lines_lang

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
	minutes, own_group = get_permitted_minutes(minutes, request, groupid)

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
