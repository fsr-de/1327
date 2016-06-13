from collections import OrderedDict

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.core.exceptions import ObjectDoesNotExist, SuspiciousOperation
from django.shortcuts import render

from _1327.minutes.models import MinutesDocument


@login_required
def list(request, groupid=None):
	if groupid:
		groupid = int(groupid)
		try:
			Group.objects.get(id=groupid)
		except ObjectDoesNotExist:
			raise SuspiciousOperation
	groups = {}
	minutes = MinutesDocument.objects.order_by('-date')
	for m in minutes:
		if not request.user.has_perm(m, MinutesDocument.get_view_permission()):
			continue

		for group in m.groups.all():
			if groupid and groupid != group.id:
				continue
			if group.name not in groups:
				groups[group.name] = {}
			if m.date.year not in groups[group.name]:
				groups[group.name][m.date.year] = []
			groups[group.name][m.date.year].append(m)
	result = OrderedDict()
	if settings.STAFF_GROUP_NAME in groups:
		result[settings.STAFF_GROUP_NAME] = groups[settings.STAFF_GROUP_NAME]
		del groups[settings.STAFF_GROUP_NAME]
	sorted_groups = sorted(groups, key=lambda s: s.lower())
	for groupname in sorted_groups:
		result[groupname] = groups[groupname]
	return render(request, "minutes_list.html", {
		'minutes': result,
	})
