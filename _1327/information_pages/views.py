from django.shortcuts import render

from guardian.shortcuts import get_objects_for_user

from _1327.information_pages.models import InformationDocument


# shows a list of information documents that are not accessible via a menu entry
def unlinked_list(request):
	if InformationDocument.objects.exists():
		permission_name = InformationDocument.objects.first().edit_permission_name  # the property can only be accessed from an instance of the class
		information_pages = get_objects_for_user(request.user, permission_name, klass=InformationDocument.objects.filter(menu_items__isnull=True)).order_by('title')
	else:
		information_pages = []

	return render(request, "unlinked_list.html", {
		'information_pages': information_pages,
	})
