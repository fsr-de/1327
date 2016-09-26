from django.contrib.auth.models import Group
from django.core.exceptions import ObjectDoesNotExist, SuspiciousOperation
from django.shortcuts import render

from guardian.shortcuts import get_objects_for_group

from _1327.minutes.models import MinutesDocument


def list(request, groupid):
	groupid = int(groupid)
	try:
		group = Group.objects.get(id=groupid)
	except ObjectDoesNotExist:
		raise SuspiciousOperation
	result = {}
	# we show all documents for which the requested group has edit permissions
	# e.g. if you request FSR minutes, all minutes for which the FSR group has edit rights will be shown
	minutes = get_objects_for_group(group, "minutes.change_minutesdocument", MinutesDocument).order_by('-date')
	for m in minutes:
		if not request.user.has_perm(MinutesDocument.get_view_permission(), m):
			continue
		if m.date.year not in result:
			result[m.date.year] = []
		result[m.date.year].append(m)
	return render(request, "minutes_list.html", {
		'minutes': result,
	})
