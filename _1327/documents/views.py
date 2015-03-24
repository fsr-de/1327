from django.shortcuts import get_object_or_404, Http404
from django.http import HttpResponse, HttpResponseServerError, HttpResponseBadRequest
from django.db import transaction
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType

import reversion
from reversion.models import RevertError

from _1327.documents.models import Document
from _1327.user_management.models import UserProfile
from _1327.user_management.shortcuts import get_object_or_error


def revert(request):
	if not request.is_ajax() or not request.POST:
		raise Http404

	version_id = request.POST['id']
	document_url_title = request.POST['url_title']
	document = get_object_or_error(Document, request.user, ['change_document'], url_title=document_url_title)
	versions = reversion.get_for_object(document)

	# find the we want to revert to
	revert_version = None
	for version in versions:
		if version.pk == int(version_id):
			revert_version = version
			break

	if revert_version is None:
		# user supplied version_id that does not exist
		return HttpResponseBadRequest('Could not find document')

	try:
		revert_version.revision.revert(delete=True)
	except RevertError:
		return HttpResponseServerError('Could not revert the version')

	fields = revert_version.field_dict
	document_class = ContentType.objects.get_for_id(fields.pop('polymorphic_ctype')).model_class()

	# Remove all references to parent objects.
	keys_to_remove = []
	for key in fields.keys():
		if "_ptr" in key:
			keys_to_remove.append(key)
	for key in keys_to_remove:
		fields.pop(key)

	reverted_document = document_class(author_id=fields.pop('author'), **fields)
	with transaction.atomic(), reversion.create_revision():
				reverted_document.save()
				reversion.set_user(request.user)
				reversion.set_comment(_('reverted to revision \"{revision_comment}\"'.format(revision_comment=revert_version.revision.comment)))

	return HttpResponse()
