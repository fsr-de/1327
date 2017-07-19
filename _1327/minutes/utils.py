from guardian.core import ObjectPermissionChecker

from _1327.minutes.models import MinutesDocument


def get_last_minutes_document_for_group(group):
	minutes = MinutesDocument.objects.all().order_by('-date')
	group_checker = ObjectPermissionChecker(group)
	group_checker.prefetch_perms(minutes)

	for m in minutes:
		if group_checker.has_perm(m.edit_permission_name, m):
			return m

	return None
