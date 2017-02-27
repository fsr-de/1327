from django.contrib.auth.models import Group
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import Http404, render
from guardian.core import ObjectPermissionChecker

from _1327.minutes.models import MinutesDocument


def list(request, groupid):
	groupid = int(groupid)
	try:
		group = Group.objects.get(id=groupid)
	except ObjectDoesNotExist:
		raise Http404
	result = {}

	own_group = request.user.is_superuser or group in request.user.groups.all()
	minutes = MinutesDocument.objects.all().prefetch_related('labels').order_by('-date')
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

	for m in minutes:
		# we show all documents for which the requested group has edit permissions
		# e.g. if you request FSR minutes, all minutes for which the FSR group has edit rights will be shown
		if not group_checker.has_perm(m.edit_permission_name, m):
			continue
		# we only show documents for which the user has view permissions
		if not user_checker.has_perm(MinutesDocument.get_view_permission(), m) and (not ip_range_group_name or not ip_range_group_checker.has_perm(MinutesDocument.get_view_permission(), m)):
			continue
		if m.date.year not in result:
			result[m.date.year] = []
		result[m.date.year].append(m)
	return render(request, "minutes_list.html", {
		'minutes_list': sorted(result.items(), reverse=True),
		'own_group': own_group
	})
