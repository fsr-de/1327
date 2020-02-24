import re

from django.shortcuts import render
from django.utils.translation import get_language
from guardian.shortcuts import get_objects_for_user

from _1327.information_pages.models import InformationDocument


# shows a list of information documents that are not accessible via a menu entry
def unlinked_list(request):
	if InformationDocument.objects.exists():
		permission_name = InformationDocument.objects.first().edit_permission_name  # the property can only be accessed from an instance of the class
		menu_pages = get_objects_for_user(request.user, permission_name, klass=InformationDocument.objects.filter(is_menu_page=True))

		# parse all menu pages for ids to linked documents and collect them in a list
		menu_page_document_ids = set()
		for menu_page in menu_pages:
			for document_id in re.findall(r"\(document:([0-9]+)\)", menu_page.text):
				try:
					menu_page_document_ids.add(int(document_id))
				except ValueError:
					pass

		title_string = "title_" + ("de" if (get_language() or "en").split('-')[0] == "de" else "en")
		non_menu_item_documents = InformationDocument.objects.filter(menu_items__isnull=True).exclude(id__in=menu_page_document_ids)
		unlinked_information_pages = get_objects_for_user(request.user, permission_name, klass=non_menu_item_documents).order_by(title_string)
	else:
		unlinked_information_pages = []

	return render(request, "unlinked_list.html", {
		'information_pages': unlinked_information_pages,
	})
