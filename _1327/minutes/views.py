from collections import OrderedDict

from django.conf import settings
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
	minutes = get_objects_for_group(group, "minutes.change_minutesdocument", MinutesDocument).order_by('-date')
	for m in minutes:
		if m.date.year not in result:
			result[m.date.year] = []
		result[m.date.year].append(m)
	return render(request, "minutes_list.html", {
		'minutes': result,
	})
