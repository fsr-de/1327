from django.contrib.auth.models import Group
from django.core.exceptions import ObjectDoesNotExist, SuspiciousOperation
from django.shortcuts import render

from guardian.core import ObjectPermissionChecker

from _1327.minutes.models import MinutesDocument


def list(request, groupid):
	groupid = int(groupid)
	try:
		group = Group.objects.get(id=groupid)
	except ObjectDoesNotExist:
		raise SuspiciousOperation
	result = {}

	minutes = MinutesDocument.objects.all().prefetch_related('labels').order_by('-date')
	# Prefetch group permissions
	group_checker = ObjectPermissionChecker(group)
	group_checker.prefetch_perms(minutes)

	# Prefetch user permissions
	user_checker = ObjectPermissionChecker(request.user)
	user_checker.prefetch_perms(minutes)

	for m in minutes:
		# we show all documents for which the requested group has edit permissions
		# e.g. if you request FSR minutes, all minutes for which the FSR group has edit rights will be shown
		if not group_checker.has_perm("minutes.change_minutesdocument", m):
			continue
		# we only show documents for which the user has view permissions
		if not user_checker.has_perm(MinutesDocument.get_view_permission(), m):
			continue
		if m.date.year not in result:
			result[m.date.year] = []
		result[m.date.year].append(m)
	return render(request, "minutes_list.html", {
		'minutes_list': sorted(result.items(), reverse=True),
	})
