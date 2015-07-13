from django.contrib import messages
from django.shortcuts import get_object_or_404, Http404
from django.http import HttpResponse, HttpResponseServerError, HttpResponseBadRequest, HttpResponseForbidden
from django.db import transaction, models
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType

import reversion
import os
from reversion.models import RevertError
from sendfile import sendfile
from _1327 import settings

from _1327.documents.models import Document, Attachment
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

	# Remove all references to parent objects, rename ForeignKeyFields, extract ManyToManyFields.
	new_fields = fields.copy()
	many_to_many_fields = {}
	for key in fields.keys():
		if "_ptr" in key:
			del new_fields[key]
			continue
		if hasattr(document_class, key):
			field = getattr(document_class, key).field
			if isinstance(field, models.ManyToManyField):
				many_to_many_fields[key] = fields[key]
			else:
				new_fields[field.attname] = fields[key]
			del new_fields[key]

	reverted_document = document_class(**new_fields)
	with transaction.atomic(), reversion.create_revision():
		reverted_document.save()
		# Restore ManyToManyFields
		for key in many_to_many_fields.keys():
			getattr(reverted_document, key).clear()
			getattr(reverted_document, key).add(*many_to_many_fields[key])
		reversion.set_user(request.user)
		reversion.set_comment(
			_('reverted to revision \"{revision_comment}\"'.format(revision_comment=revert_version.revision.comment)))

	return HttpResponse()


def delete_attachment(request):
	if request.is_ajax() and request.method == "POST":
		attachment = Attachment.objects.get(id=request.POST['id'])
		# check whether user has permission to change the document the attachment belongs to
		document = attachment.document
		if not document.can_be_changed_by(request.user):
			return HttpResponseForbidden()

		attachment.file.delete()
		attachment.delete()
		messages.success(request, _("Successfully deleted Attachment!"))
		return HttpResponse()
	raise Http404()


def download_attachment(request):
	if not request.method == "GET":
		return HttpResponseBadRequest()

	attachment = get_object_or_404(Attachment, pk=request.GET['attachment_id'])
	# check whether user is allowed to see that document and thus download the attachment
	document = attachment.document
	if not request.user.has_perm(document.VIEW_PERMISSION_NAME, document):
		return HttpResponseForbidden()

	filename = os.path.join(settings.MEDIA_ROOT, attachment.file.name)
	return sendfile(request, filename, attachment=True, attachment_filename=attachment.displayname)


def update_attachment_order(request):
	data = request.POST
	if data is None or not request.is_ajax():
		raise Http404

	for pk, index in data._iteritems():
		attachment = get_object_or_404(Attachment, pk=pk)
		# check that user is allowed to make changes to attachment
		document = attachment.document
		if not document.can_be_changed_by(request.user):
			return HttpResponseForbidden()

		attachment.index = index
		attachment.save()
	return HttpResponse()
