from django.template import loader
from guardian.shortcuts import get_objects_for_user

from _1327.information_pages.models import InformationDocument
from _1327.minutes.models import MinutesDocument
from _1327.polls.models import Poll


def get_document_selection(request):
	minutes = get_objects_for_user(
		request.user,
		MinutesDocument.VIEW_PERMISSION_NAME,
		klass=MinutesDocument.objects.all()
	)
	information_documents = get_objects_for_user(
		request.user,
		InformationDocument.VIEW_PERMISSION_NAME,
		klass=InformationDocument.objects.all()
	)
	polls = get_objects_for_user(
		request.user,
		Poll.VIEW_PERMISSION_NAME,
		klass=Poll.objects.all()
	)

	template = loader.get_template("search_api.json")
	return template.render(
		{
			'minutes': minutes,
			'information_documents': information_documents,
			'polls': polls,
			'id_only': True,
		},
		request,
	)
