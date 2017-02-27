import json
import tempfile

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.files.base import ContentFile
from django.core.urlresolvers import reverse
from django.db import transaction
from django.test import TestCase
from django_webtest import WebTest
from guardian.shortcuts import assign_perm, get_perms, get_perms_for_model, remove_perm
import markdown
from model_mommy import mommy
from reversion import revisions

from _1327.documents.markdown_internal_link_extension import InternalLinksMarkdownExtension
from _1327.information_pages.models import InformationDocument
from _1327.main.utils import slugify
from _1327.minutes.models import MinutesDocument
from _1327.polls.models import Poll
from _1327.user_management.models import UserProfile

from .models import Attachment, Document, TemporaryDocumentText


class TestInternalLinkMarkDown(TestCase):
	def setUp(self):
		self.user = mommy.make(UserProfile, is_superuser=True)

		self.md = markdown.Markdown(safe_mode='escape', extensions=[InternalLinksMarkdownExtension(), 'markdown.extensions.tables'])

		document = mommy.prepare(InformationDocument, text="text")
		with transaction.atomic(), revisions.create_revision():
				document.save()
				revisions.set_user(self.user)
				revisions.set_comment('test version')

	def test_information_documents(self):
		document = InformationDocument.objects.get()
		text = self.md.convert('[description](document:' + str(document.id) + ')')
		link = reverse(document.get_view_url_name(), args=[document.url_title])
		self.assertIn('<a href="' + link + '">description</a>', text)

	def test_document_deleted(self):
		document = InformationDocument.objects.get()
		document.delete()
		text = self.md.convert('[description](document:{})'.format(document.id))
		self.assertIn('<a>[missing link]</a>', text)


class TestRevertion(WebTest):
	csrf_checks = False

	def setUp(self):
		self.user = mommy.make(UserProfile, is_superuser=True)

		document = mommy.prepare(Document, text="text")
		with transaction.atomic(), revisions.create_revision():
				document.save()
				revisions.set_user(self.user)
				revisions.set_comment('test version')

		# create a second version
		document.text += '\nmore text'
		with transaction.atomic(), revisions.create_revision():
				document.save()
				revisions.set_user(self.user)
				revisions.set_comment('added more text')

	def test_only_admin_may_revert(self):
		document = Document.objects.get()
		versions = revisions.get_for_object(document)
		self.assertEqual(len(versions), 2)

		user_without_perms = mommy.make(UserProfile)
		response = self.app.post(
			reverse('documents:revert'), {'id': versions[1].pk, 'url_title': document.url_title},
			status=404,
			user=user_without_perms,
		)
		self.assertEqual(response.status_code, 404)

		response = self.app.post(
			reverse('documents:revert'), {'id': versions[1].pk, 'url_title': document.url_title},
			status=403,
			xhr=True,
			user=user_without_perms,
		)
		self.assertEqual(response.status_code, 403)

		response = self.app.post(reverse('documents:revert'), {'id': versions[1].pk, 'url_title': document.url_title}, user=self.user, status=404)
		self.assertEqual(response.status_code, 404)

		response = self.app.post(reverse('documents:revert'), {'id': versions[1].pk, 'url_title': document.url_title}, user=self.user, xhr=True)
		self.assertEqual(response.status_code, 200)

	def test_revert_document(self):
		document = Document.objects.get()
		versions = revisions.get_for_object(document)
		self.assertEqual(len(versions), 2)

		# second step try to revert to old version
		response = self.app.post(reverse('documents:revert'), {'id': versions[1].pk, 'url_title': document.url_title}, user=self.user, xhr=True)
		self.assertEqual(response.status_code, 200)

		versions = revisions.get_for_object(document)
		self.assertEqual(len(versions), 3)
		self.assertEqual(versions[0].object.text, "text")
		self.assertEqual(versions[0].revision.comment, 'reverted to revision "test version"')

	def test_revert_to_different_url(self):
		document = Document.objects.get()
		old_url = document.url_title

		document.url_title = 'new/url'
		with transaction.atomic(), revisions.create_revision():
			document.save()
			revisions.set_user(self.user)
			revisions.set_comment('changed url')

		versions = revisions.get_for_object(document)
		response = self.app.post(reverse('documents:revert'), {'id': versions[2].pk, 'url_title': document.url_title}, user=self.user, xhr=True)

		self.assertEqual(response.status_code, 200)
		self.assertIn(reverse('versions', args=[old_url]), response.body.decode('utf-8'))


class TestAutosave(WebTest):
	csrf_checks = False
	extra_environ = {'HTTP_ACCEPT_LANGUAGE': 'en'}

	def setUp(self):
		self.user = mommy.make(UserProfile, is_superuser=True)

		document = mommy.prepare(InformationDocument, text="text")
		with transaction.atomic(), revisions.create_revision():
				document.save()
				revisions.set_user(self.user)
				revisions.set_comment('test version')

	def test_autosave(self):
		# get document
		document = Document.objects.get()

		# document text should be text
		response = self.app.get(reverse(document.get_edit_url_name(), args=[document.url_title]), user=self.user)
		self.assertEqual(response.status_code, 200)
		form = response.forms['document-form']
		self.assertEqual(form.get('text').value, 'text')

		# autosave AUTO
		response = self.app.post(reverse('documents:autosave', args=[document.url_title]), {'text': 'AUTO', 'title': form.get('title').value, 'comment': ''}, user=self.user, xhr=True)
		self.assertEqual(response.status_code, 200)

		# if not loading autosave text should be still text
		response = self.app.get(reverse(document.get_edit_url_name(), args=[document.url_title]), user=self.user)
		self.assertEqual(response.status_code, 200)
		form = response.forms['document-form']
		self.assertEqual(form.get('text').value, 'text')

		# if loading autosave text should be AUTO
		response = self.app.get(reverse(document.get_edit_url_name(), args=[document.url_title]), {'restore': ''}, user=self.user)
		self.assertEqual(response.status_code, 200)
		form = response.forms['document-form']
		self.assertEqual(form.get('text').value, 'AUTO')

		# second autosave AUTO2
		response = self.app.post(reverse('documents:autosave', args=[document.url_title]), {'text': 'AUTO2', 'title': form.get('title').value, 'comment': ''}, user=self.user, xhr=True)
		self.assertEqual(response.status_code, 200)

		# if loading autosave text should be AUTO2
		response = self.app.get(reverse(document.get_edit_url_name(), args=[document.url_title]), {'restore': ''}, user=self.user)
		self.assertEqual(response.status_code, 200)
		form = response.forms['document-form']
		self.assertEqual(form.get('text').value, 'AUTO2')

	def test_autosave_newPage(self):
		# create document
		response = self.app.get(reverse('documents:create', args=['informationdocument']), user=self.user)
		self.assertEqual(response.status_code, 200)
		form = response.forms['document-form']
		url_title = slugify(form.get('title').value)

		# autosave AUTO
		response = self.app.post(reverse('documents:autosave', args=[url_title]), {'text': 'AUTO', 'title': form.get('title').value, 'comment': ''}, xhr=True)
		self.assertEqual(response.status_code, 200)

		# on the new page site should be a banner with a restore link
		response = self.app.get(reverse('documents:create', args=['informationdocument']), user=self.user)
		self.assertEqual(response.status_code, 200)
		self.assertIn((reverse('edit', args=[url_title]) + '?restore'), str(response.body))

		user2 = mommy.make(UserProfile, is_superuser=True)
		# on the new page site should be a banner with a restore link but not for another user
		response = self.app.get(reverse('documents:create', args=['informationdocument']), user=user2)
		self.assertEqual(response.status_code, 200)
		self.assertNotIn((reverse('edit', args=[url_title]) + '?restore'), str(response.body))

		# create second document
		response = self.app.get(reverse('documents:create', args=['informationdocument']), user=self.user)
		self.assertEqual(response.status_code, 200)
		form = response.forms['document-form']
		url_title2 = slugify(form.get('title').value)

		# autosave second document AUTO
		response = self.app.post(reverse('documents:autosave', args=[url_title2]), {'text': 'AUTO', 'title': form.get('title').value, 'comment': ''}, user=self.user, xhr=True)
		self.assertEqual(response.status_code, 200)

		# on the new page site should be a banner with a restore link for both sites
		response = self.app.get(reverse('documents:create', args=['informationdocument']), user=self.user)
		self.assertIn((reverse('edit', args=[url_title]) + '?restore'), str(response.body))
		self.assertIn((reverse('edit', args=[url_title2]) + '?restore'), str(response.body))

		# if not loading autosave text should be still empty
		response = self.app.get(reverse('edit', args=[url_title]), user=self.user)
		self.assertEqual(response.status_code, 200)
		form = response.forms['document-form']
		self.assertEqual(form.get('text').value, '')

		# if loading autosave text should be AUTO
		response = self.app.get(reverse('edit', args=[url_title]), {'restore': ''}, user=self.user)
		self.assertEqual(response.status_code, 200)
		form = response.forms['document-form']
		self.assertEqual(form.get('text').value, 'AUTO')

	def test_autosave_with_different_document_types(self):
		# create document
		response = self.app.get(reverse('documents:create', args=['informationdocument']), user=self.user)
		self.assertEqual(response.status_code, 200)
		form = response.forms['document-form']
		url_title = slugify(form.get('title').value)

		# autosave AUTO
		response = self.app.post(reverse('documents:autosave', args=[url_title]), {'text': 'AUTO', 'title': form.get('title').value, 'comment': '', 'group': mommy.make(Group)}, xhr=True)
		self.assertEqual(response.status_code, 200)

		# there should be no restore link on creation page for different document type
		response = self.app.get(reverse('documents:create', args=['poll']), user=self.user)
		self.assertNotIn((reverse('edit', args=[url_title]) + '?restore'), str(response.body))

		# on the new page site should be a banner with a restore link
		response = self.app.get(reverse('documents:create', args=['informationdocument']), user=self.user)
		self.assertEqual(response.status_code, 200)
		self.assertIn((reverse('edit', args=[url_title]) + '?restore'), str(response.body))

	def test_autosave_not_possible_to_view_without_permissions(self):
		document = Document.objects.get()
		autosave = mommy.make(TemporaryDocumentText, document=document, author=self.user)

		self.assertFalse(document.has_perms())

		user_without_permissions = mommy.make(UserProfile)
		response = self.app.get(
			reverse(autosave.document.get_edit_url_name(), args=[autosave.document.url_title]),
			expect_errors=True,
			user=user_without_permissions
		)
		self.assertEqual(response.status_code, 403)

	def test_autosave_possible_to_view_autosave_with_permissions(self):
		document = Document.objects.get()
		autosave = mommy.make(TemporaryDocumentText, document=document, author=self.user)

		self.assertFalse(document.has_perms())
		assign_perm(document.add_permission_name, self.user)

		response = self.app.get(reverse(autosave.document.get_edit_url_name(), args=[autosave.document.url_title]), user=self.user)
		self.assertEqual(response.status_code, 200)
		self.assertIn("This document was autosaved on", response.body.decode('utf-8'))

	def test_autosave_not_possible_to_view_because_not_author(self):
		document = Document.objects.get()
		autosave = mommy.make(TemporaryDocumentText, document=document)

		self.assertFalse(document.has_perms())

		response = self.app.get(reverse(autosave.document.get_edit_url_name(), args=[autosave.document.url_title]), expect_errors=True, user=self.user)
		self.assertEqual(response.status_code, 403)


class TestMarkdownRendering(WebTest):
	csrf_checks = False

	def setUp(self):
		self.user = mommy.make(UserProfile, is_superuser=True)
		self.document_text = 'test'
		self.document = mommy.make(InformationDocument, text=self.document_text)
		self.document.set_all_permissions(mommy.make(Group))

	def test_render_text_no_permission(self):
		user_without_permission = mommy.make(UserProfile)
		response = self.app.post(
			reverse('documents:render', args=[self.document.url_title]),
			{'text': self.document_text},
			xhr=True,
			expect_errors=True,
			user=user_without_permission
		)
		self.assertEqual(response.status_code, 403)

	def test_render_text_wrong_method(self):
		response = self.app.get(reverse('documents:render', args=[self.document.url_title]), {'text': self.document_text}, user=self.user, xhr=True, expect_errors=True)
		self.assertEqual(response.status_code, 400)

	def test_render_text(self):
		response = self.app.post(reverse('documents:render', args=[self.document.url_title]), {'text': self.document_text}, user=self.user, xhr=True)
		self.assertEqual(response.status_code, 200)
		self.assertEqual('<p>' + self.document_text + '</p>', response.body.decode('utf-8'))


class TestSignals(TestCase):
	def setUp(self):
		self.user = mommy.make(UserProfile, is_superuser=True)

	def test_slugify_hook(self):
		# create a new document for every subclass of document
		# and see whether the url_title is automatically created
		for obj_id, subclass in enumerate(Document.__subclasses__()):
			new_document = mommy.make(subclass, title="test_{}".format(obj_id), url_title="")
			self.assertEqual(new_document.url_title, "test_{}".format(obj_id))

	def test_group_permission_hook(self):
		# for every subclass of a document check whether the permission hook works
		document_subclass_permissions = []
		for obj_id, subclass in enumerate(Document.__subclasses__()):
			# create a new group that only receives permissions for the current subclass
			group = Group.objects.create(name="test_group_{}".format(obj_id))
			model_permissions = get_perms_for_model(subclass)
			document_subclass_permissions.extend(model_permissions)
			# assign all possible permissions to that group
			for permission in model_permissions:
				permission_name = "{}.{}".format(permission.content_type.app_label, permission.codename)
				assign_perm(permission_name, group)

			# test whether the permission hook works
			test_object = mommy.make(subclass, title="test")
			user_permissions = get_perms(group, test_object)
			self.assertNotEqual(len(user_permissions), 0)

			for permission in group.permissions.all():
				self.assertIn(permission.codename, user_permissions)

	def test_possibility_to_change_permission_for_groups(self):
		group = mommy.make(Group, name="FSR")
		test_user = mommy.make(UserProfile)
		test_user.groups.add(group)
		test_user.save()

		model_permissions = get_perms_for_model(InformationDocument)
		permission_names = []
		for permission in model_permissions:
			permission_name = "{}.{}".format(permission.content_type.app_label, permission.codename)
			assign_perm(permission_name, group)
			permission_names.append(permission_name)

		# test whether we can remove a permission from the group
		# the permission should not be added again
		test_object = mommy.make(InformationDocument)
		self.assertTrue(test_user.has_perm(permission_names[0], test_object))
		remove_perm(permission_names[0], group, test_object)
		test_object.save()
		self.assertFalse(test_user.has_perm(permission_names[0], test_object))


class TestSubclassConstraints(TestCase):
	def is_abstract_model(self, cls):
		return hasattr(cls._meta, "abstract") and cls._meta.abstract

	def has_permissions(self, cls):
		return hasattr(cls._meta, "permissions")

	def test_document_subclasses_override_get_url_method(self):
		for subclass in Document.__subclasses__():
			if self.is_abstract_model(subclass):
				# abstract classes do not have to override the get_url method
				continue

			msg = "All non-abstract subclasses of Document should override the get_url method"
			self.assertIsNot(subclass.get_view_url, Document.get_view_url, msg=msg)

	def test_view_permissions(self):
		for subclass in Document.__subclasses__():
			if self.is_abstract_model(subclass):
				continue

			self.assertTrue(self.has_permissions(subclass), msg="All Document subclasses must specify permissions in their Meta class")
			self.assertTrue(hasattr(subclass, "VIEW_PERMISSION_NAME"), msg="All Document subclasses must specify a VIEW_PERMISSION_NAME field")

			permission_names = [permission[0] for permission in subclass._meta.permissions]
			self.assertIn(subclass.VIEW_PERMISSION_NAME, permission_names, msg="All Document subclasses must declare the permission named in VIEW_PERMISSION_NAME")


class TestAttachments(WebTest):
	"""
		Tests creating, viewing and deleting attachments
		InformationDocuments are used as testclass. It is assumed that the behavior is similar with other documenttypes
	"""
	csrf_checks = False

	def setUp(self):
		self.user = mommy.make(UserProfile, is_superuser=True)

		self.group = mommy.make(Group, make_m2m=True)
		for permission in get_perms_for_model(InformationDocument):
			permission_name = "{}.{}".format(permission.content_type.app_label, permission.codename)
			assign_perm(permission_name, self.group)
		self.group.save()

		self.group_user = mommy.make(UserProfile)
		self.group_user.groups.add(self.group)
		self.group_user.save()

		self.document = mommy.make(InformationDocument)

		self.content = "test content of test attachment"
		attachment_file = ContentFile(self.content)
		self.attachment = mommy.make(Attachment, document=self.document, displayname="test")  # displayname does not include the extension
		self.attachment.file.save('temp.txt', attachment_file)
		self.attachment.save()

	def tearDown(self):
		for attachment in self.document.attachments.all():
			attachment.file.delete()
		self.attachment.file.delete()

	def test_create_attachment(self):
		upload_files = [
			('file', 'test.txt', bytes(tempfile.SpooledTemporaryFile(max_size=10000, prefix='txt', mode='r')))
		]

		# test that user who has no change permission on a document can not add an attachment
		# and neither see the corresponding page
		normal_user = mommy.make(UserProfile)

		response = self.app.get(
			reverse(self.document.get_attachments_url_name(), args=[self.document.url_title]),
			user=normal_user,
			expect_errors=True
		)
		self.assertEqual(response.status_code, 403)

		response = self.app.post(
			reverse(self.document.get_attachments_url_name(), args=[self.document.url_title]),
			content_type='multipart/form-data',
			upload_files=upload_files,
			user=normal_user,
			expect_errors=True
		)
		self.assertEqual(response.status_code, 403)

		# test that user who is allowed to view the document may not add attachments to it
		# and neither see the corresponding page
		assign_perm("view_informationdocument", normal_user, self.document)

		response = self.app.get(
			reverse(self.document.get_attachments_url_name(), args=[self.document.url_title]),
			user=normal_user,
			expect_errors=True
		)
		self.assertEqual(response.status_code, 403)

		response = self.app.post(
			reverse(self.document.get_attachments_url_name(), args=[self.document.url_title]),
			content_type='multipart/form-data',
			upload_files=upload_files,
			user=normal_user,
			expect_errors=True
		)
		self.assertEqual(response.status_code, 403)

		# test that member of group who has according permissions is allowed to upload attachments
		# and to see the corresponding page
		response = self.app.get(reverse(self.document.get_attachments_url_name(), args=[self.document.url_title]), user=self.group_user)
		self.assertEqual(response.status_code, 200)

		response = self.app.post(
			reverse(self.document.get_attachments_url_name(), args=[self.document.url_title]),
			content_type='multipart/form-data',
			upload_files=upload_files,
			user=self.group_user
		)
		self.assertEqual(response.status_code, 200)

		# test that superuser is allowed to upload attachments and to see the corresponding page
		response = self.app.get(reverse(self.document.get_attachments_url_name(), args=[self.document.url_title]), user=self.user)
		self.assertEqual(response.status_code, 200)

		response = self.app.post(
			reverse(self.document.get_attachments_url_name(), args=[self.document.url_title]),
			content_type='multipart/form-data',
			upload_files=upload_files,
			user=self.user
		)
		self.assertEqual(response.status_code, 200)

	def test_delete_attachment(self):
		params = {
			'id': self.attachment.id,
		}

		# try to delete an attachment as user with no permissions at all (anonymous user)
		response = self.app.get(reverse('documents:delete_attachment'), params=params, expect_errors=True)
		self.assertEqual(response.status_code, 404, msg="GET Requests are not allowed to work")

		response = self.app.get(reverse('documents:delete_attachment'), params=params, expect_errors=True, xhr=True)
		self.assertEqual(response.status_code, 404, msg="GET Requests are not allowed to work")

		response = self.app.post(reverse('documents:delete_attachment'), params=params, expect_errors=True)
		self.assertEqual(response.status_code, 404, msg="Requests that are not AJAX should return a 404 error")

		response = self.app.post(reverse('documents:delete_attachment'), params=params, expect_errors=True, xhr=True)
		redirect_url = reverse('login') + '?next=' + reverse('documents:delete_attachment')
		self.assertRedirects(
			response,
			redirect_url,
			msg_prefix="If the site is visited by anonymous users they should see the login page"
		)

		# try to delete an attachment as user with no permissions
		normal_user = mommy.make(UserProfile)
		response = self.app.post(reverse('documents:delete_attachment'), params=params, expect_errors=True, xhr=True, user=normal_user)
		self.assertEqual(
			response.status_code,
			403,
			msg="If users have no permissions they should not be able to delete an attachment"
		)

		# try to delete an attachment as user with wrong permissions
		assign_perm(InformationDocument.get_view_permission(), normal_user, self.document)
		response = self.app.post(reverse('documents:delete_attachment'), params=params, expect_errors=True, xhr=True, user=normal_user)
		self.assertEqual(
			response.status_code,
			403,
			msg="If users has no permissions they should not be able to delete an attachment"
		)

		# try to delete an attachment as user with correct permissions
		response = self.app.post(reverse('documents:delete_attachment'), params=params, xhr=True, user=self.group_user)
		self.assertEqual(
			response.status_code,
			200,
			msg="Users with the correct permissions for a document should be able to delete an attachment"
		)

		# re create the attachment
		self.attachment.save()

		# try to delete an attachment as superuser
		response = self.app.post(reverse('documents:delete_attachment'), params=params, xhr=True, user=self.user)
		self.assertEqual(
			response.status_code,
			200,
			msg="Users with the correct permissions for a document should be able to delete an attachment"
		)

	def test_view_attachment(self):
		params = {
			'hash_value': self.attachment.hash_value,
		}

		# test that a user with insufficient permissions is not allowed to view/download an attachment
		# be an anonymous user
		response = self.app.post(reverse('documents:download_attachment'), params=params, expect_errors=True)
		self.assertEqual(response.status_code, 400, msg="Should be bad request as user used wrong request method")

		response = self.app.get(reverse('documents:download_attachment'), params=params, expect_errors=True)
		self.assertEqual(response.status_code, 302)
		response = response.follow()
		self.assertTemplateUsed(response, 'login.html', msg_prefix="Anonymous users should see the login page")

		# test viewing an attachment using a user with insufficient permissions
		normal_user = mommy.make(UserProfile)
		assign_perm('change_informationdocument', normal_user, self.document)

		response = self.app.get(reverse('documents:download_attachment'), params=params, expect_errors=True, user=normal_user)
		self.assertEqual(response.status_code, 403, msg="Should be forbidden as user has insufficient permissions")

		# grant the correct permission to the user an try again
		assign_perm(InformationDocument.get_view_permission(), normal_user, self.document)

		response = self.app.get(reverse('documents:download_attachment'), params=params, user=normal_user)
		self.assertEqual(
			response.status_code,
			200,
			msg="Users with sufficient permissions should be able to download an attachment"
		)
		self.assertEqual(
			response.body.decode('utf-8'),
			self.content,
			msg="An attachment that has been downloaded should contain its original content"
		)
		self.assertEqual(
			response.headers['Content-Disposition'],
			"attachment; filename=\"b\'test.txt\'\"; filename*=UTF-8\'\'test.txt",
			msg="The filename should include the file extension although not included in the displayname"
		)

		# try the same with a user that is in a group having the correct permission
		response = self.app.get(reverse('documents:download_attachment'), params=params, user=self.group_user)
		self.assertEqual(
			response.status_code,
			200,
			msg="Users with sufficient permissions should be able to download an attachment"
		)
		self.assertEqual(
			response.body.decode('utf-8'),
			self.content,
			msg="An attachment that has been downloaded should contain its original content"
		)

		# make sure that a superuser is always allowed to download an attachment
		response = self.app.get(reverse('documents:download_attachment'), params=params, user=self.user)
		self.assertEqual(
			response.status_code,
			200,
			msg="Users with sufficient permissions should be able to download an attachment"
		)
		self.assertEqual(
			response.body.decode('utf-8'),
			self.content,
			msg="An attachment that has been downloaded should contain its original content"
		)

	def test_sort_attachments(self):
		mommy.make(Attachment, _quantity=3, document=self.document)

		attachments = Attachment.objects.all()
		old_attachment_order = {}
		for index, attachment in enumerate(attachments):
			self.assertEqual(attachment.index, 0)
			attachment.index = index
			attachment.save()
			old_attachment_order[attachment.id] = index

		# reverse ordering of attachments
		attachments = Attachment.objects.all().order_by('-index')
		new_attachment_order = {}
		for index, attachment in enumerate(attachments):
			new_attachment_order[attachment.id] = index

		response = self.app.post(
			reverse('documents:update_attachment_order'),
			new_attachment_order,
			xhr=True,
			user=self.user,
		)
		self.assertEqual(response.status_code, 200)

		# check that all indices changed
		attachments = Attachment.objects.all().order_by('index')
		for attachment in attachments:
			self.assertNotEqual(
				attachment.index,
				old_attachment_order[attachment.id],
				msg="Old id and new id should not be the same",
			)

	def test_attachment_change_no_direct_download(self):
		self.assertFalse(self.attachment.no_direct_download, "attachments can be downloaded directly by default")
		response = self.app.post(
			reverse('documents:change_attachment'),
			{'id': self.attachment.id, 'no_direct_download': 'false'},
			user=self.user,
			xhr=True,
		)
		self.assertEqual(response.status_code, 200, "it should be possible to change the direct download state")
		attachment = Attachment.objects.get(pk=self.attachment.id)
		self.assertFalse(attachment.no_direct_download)

	def test_attachment_change_no_direct_download_wrong_permissions(self):
		self.assertFalse(self.attachment.no_direct_download)
		user = mommy.make(UserProfile)
		response = self.app.post(
			reverse('documents:change_attachment'),
			{'id': self.attachment.id, 'no_direct_download': 'false'},
			user=user,
			xhr=True,
			expect_errors=True
		)
		self.assertEqual(response.status_code, 403)

	def test_attachment_change_no_direct_download_wrong_request_type(self):
		response = self.app.get(
			reverse('documents:change_attachment'),
			{'id': self.attachment.id, 'no_direct_download': 'false'},
			user=self.user,
			xhr=True,
			expect_errors=True,
		)
		self.assertEqual(response.status_code, 404)

	def test_attachment_change_no_direct_download_no_ajax(self):
		response = self.app.post(
			reverse('documents:change_attachment'),
			{'id': self.attachment.id, 'no_direct_download': 'false'},
			user=self.user,
			expect_errors=True,
		)
		self.assertEqual(response.status_code, 404)

	def test_attachment_change_displayname(self):
		new_displayname = 'lorem ipsum'
		response = self.app.post(
			reverse('documents:change_attachment'),
			{'id': self.attachment.id, 'displayname': new_displayname},
			user=self.user,
			xhr=True,
		)
		self.assertEqual(response.status_code, 200, "it should be possible to change displayname")
		attachment = Attachment.objects.get(pk=self.attachment.id)
		self.assertEqual(attachment.displayname, new_displayname)

	def test_attachment_change_displayname_permissions(self):
		self.assertFalse(self.attachment.no_direct_download)
		user = mommy.make(UserProfile)
		new_displayname = 'lorem ipsum'
		response = self.app.post(
			reverse('documents:change_attachment'),
			{'id': self.attachment.id, 'displayname': new_displayname},
			user=user,
			xhr=True,
			expect_errors=True
		)
		self.assertEqual(response.status_code, 403)

	def test_attachment_change_displayname_wrong_request_type(self):
		new_displayname = 'lorem ipsum'
		response = self.app.get(
			reverse('documents:change_attachment'),
			{'id': self.attachment.id, 'displayname': new_displayname},
			user=self.user,
			xhr=True,
			expect_errors=True,
		)
		self.assertEqual(response.status_code, 404)

	def test_attachment_change_attachment_no_ajax(self):
		new_displayname = 'lorem ipsum'
		response = self.app.post(
			reverse('documents:change_attachment'),
			{'id': self.attachment.id, 'displayname': new_displayname},
			user=self.user,
			expect_errors=True,
		)
		self.assertEqual(response.status_code, 404)

	def test_attachment_change_no_direct_download_view(self):
		attachment = mommy.make(Attachment, document=self.document, displayname="pic.jpg", no_direct_download=True)
		response = self.app.get(
			reverse(self.document.get_view_url_name(), args=[self.document.url_title]),
			user=self.user,
		)
		self.assertEqual(response.status_code, 200)
		self.assertNotIn(attachment.displayname, response.body.decode('utf-8'))

	def test_attachment_get_all_attachments_no_images(self):
		response = self.app.get(
			reverse('documents:get_attachments', args=[self.document.id]),
			user=self.user,
			xhr=True,
		)
		self.assertEqual(response.status_code, 200)
		returned_data = json.loads(response.body.decode('utf-8'))
		self.assertEqual(len(returned_data), 0)

	def test_attachment_get_all_attachments(self):
		attachment = mommy.make(Attachment, displayname="pic.jpg", document=self.document)
		attachment.save()

		response = self.app.get(
			reverse('documents:get_attachments', args=[self.document.id]),
			user=self.user,
			xhr=True,
		)
		self.assertEqual(response.status_code, 200)
		returned_data = json.loads(response.body.decode('utf-8'))
		self.assertEqual(len(returned_data), 1)

	def test_attachment_get_all_attachments_wrong_user(self):
		user = mommy.make(UserProfile)
		response = self.app.get(
			reverse('documents:get_attachments', args=[self.document.id]),
			user=user,
			xhr=True,
			expect_errors=True,
		)
		self.assertEqual(response.status_code, 403)

	def test_attachment_get_all_attachments_no_ajax(self):
		response = self.app.get(
			reverse('documents:get_attachments', args=[self.document.id]),
			user=self.user,
			expect_errors=True,
		)
		self.assertEqual(response.status_code, 404)

	def test_attachment_get_all_attachments_no_document_id(self):
		response = self.app.get(
			reverse('documents:get_attachments', args=[self.document.id]),
			user=self.user,
			expect_errors=True,
		)
		self.assertEqual(response.status_code, 404)

	def test_create_attachment_from_editor_wrong_method(self):
		response = self.app.get(
			reverse('documents:create_attachment'),
			user=self.user,
			expect_errors=True,
		)
		self.assertEqual(response.status_code, 404)

	def test_create_attachment_from_editor_no_permission(self):
		params = {
			'document': self.document.id,
		}

		normal_user = mommy.make(UserProfile)

		response = self.app.post(
			reverse('documents:create_attachment'),
			params=params,
			user=normal_user,
			xhr=True,
			expect_errors=True
		)
		self.assertEqual(response.status_code, 403)

	def test_create_attachment_from_editor_invalid_form(self):
		upload_files = [
			('file', 'test.txt', bytes())
		]

		params = {
			'no_direct_download': True,
			'document': self.document.id,
			'displayname': '',
		}

		response = self.app.post(
			reverse('documents:create_attachment'),
			content_type='multipart/form-data',
			upload_files=upload_files,
			params=params,
			user=self.user,
			xhr=True,
			expect_errors=True
		)
		self.assertEqual(response.status_code, 400)

	def test_create_attachment_from_editor(self):
		upload_files = [
			('file', 'test.txt', bytes("Test content of file", encoding='utf-8'))
		]

		params = {
			'no_direct_download': True,
			'document': self.document.id,
			'displayname': '',
		}

		self.assertEqual(Attachment.objects.count(), 1)
		self.assertEqual(self.document.attachments.count(), 1)

		response = self.app.post(
			reverse('documents:create_attachment'),
			content_type='multipart/form-data',
			upload_files=upload_files,
			params=params,
			user=self.user,
			xhr=True,
		)
		self.assertEqual(response.status_code, 200)

		self.assertEqual(Attachment.objects.count(), 2)
		self.assertEqual(self.document.attachments.count(), 2)
		self.assertEqual(self.document.attachments.last().index, 2)


class TestDeletion(WebTest):
	csrf_checks = False

	def setUp(self):
		self.user = mommy.make(UserProfile, is_superuser=True)
		self.document = mommy.make(InformationDocument)
		self.document.set_all_permissions(mommy.make(Group))

	def test_delete_cascade(self):
		response = self.app.get(reverse("documents:get_delete_cascade", args=[self.document.url_title]), user=self.user)
		self.assertEqual(response.status_code, 200)
		data = json.loads(response.body.decode('utf-8'))
		self.assertEqual(type(self.document).__name__, data[0]["type"])

	def test_delete_cascade_nested_objects(self):
		mommy.make(Attachment, document=self.document)
		response = self.app.get(reverse("documents:get_delete_cascade", args=[self.document.url_title]), user=self.user)
		self.assertEqual(response.status_code, 200)
		data = json.loads(response.body.decode('utf-8'))
		self.assertEqual(len(data), 2)
		self.assertEqual(Attachment.__name__, data[1][0]['type'])

	def test_delete_cascade_no_permissions(self):
		user = mommy.make(UserProfile)
		response = self.app.get(reverse("documents:get_delete_cascade", args=[self.document.url_title]), user=user, expect_errors=True)
		self.assertEqual(response.status_code, 403)

	def test_delete_documents(self):
		for document_class in Document.__subclasses__():
			document = mommy.make(document_class)
			self.assertEqual(Document.objects.count(), 2)
			response = self.app.post(reverse("documents:delete_document", args=[document.url_title]), user=self.user)
			self.assertEqual(response.status_code, 200)
			self.assertEqual(Document.objects.count(), 1)

	def test_delete_documents_with_attachment(self):
		for document_class in Document.__subclasses__():
			document = mommy.make(document_class)
			self.assertEqual(Document.objects.count(), 2)
			mommy.make(Attachment, document=document)
			self.assertEqual(Attachment.objects.count(), 1)
			response = self.app.post(reverse("documents:delete_document", args=[document.url_title]), user=self.user)
			self.assertEqual(response.status_code, 200)
			self.assertEqual(Attachment.objects.count(), 0)
			self.assertEqual(Document.objects.count(), 1)

	def test_delete_documents_insufficient_permissions(self):
		user = mommy.make(UserProfile)
		for document_class in Document.__subclasses__():
			document = mommy.make(document_class)
			self.assertEqual(Document.objects.count(), 2)
			response = self.app.post(reverse("documents:delete_document", args=[document.url_title]), user=user, expect_errors=True)
			self.assertEqual(response.status_code, 403)
			self.assertEqual(Document.objects.count(), 2)
			document.delete()

	def test_delete_button_not_present_if_creating_document(self):
		# test that the delete button is not visible if the document that gets edited has no revisions
		response = self.app.get(reverse(self.document.get_edit_url_name(), args=[self.document.url_title]), user=self.user)
		self.assertEqual(response.status_code, 200)
		self.assertNotIn("deleteDocumentButton", response.body.decode('utf-8'))

	def test_delete_button_present_if_editing_already_existing_document(self):
		# test that the delete button is visible if the document has at least one revision
		response = self.app.get(reverse(self.document.get_edit_url_name(), args=[self.document.url_title]), user=self.user)

		form = response.forms['document-form']
		form['comment'] = 'new revision'
		response = form.submit().follow()
		self.assertEqual(response.status_code, 200)

		response = self.app.get(reverse(self.document.get_edit_url_name(), args=[self.document.url_title]), user=self.user)
		self.assertEqual(response.status_code, 200)
		self.assertIn("deleteDocumentButton", response.body.decode('utf-8'))


class TestPreview(WebTest):
	csrf_checks = False

	def setUp(self):
		self.document = mommy.make(Document)
		self.user = mommy.make(UserProfile, is_superuser=True)

	def test_preview_wrong_method(self):
		response = self.app.post(reverse('documents:preview') + '?hash_value={}'.format(self.document.hash_value), status=404)
		self.assertEqual(response.status_code, 404)

	def test_preview_document_does_not_exist(self):
		response = self.app.get(reverse('documents:preview') + '?hash_value={}'.format(1), status=404)
		self.assertEqual(response.status_code, 404)

	def test_preview_without_get_param(self):
		response = self.app.get(reverse('documents:preview'), status=404)
		self.assertEqual(response.status_code, 404)

	def test_preview_view(self):
		response = self.app.get(reverse('documents:preview') + '?hash_value={}'.format(self.document.hash_value))
		self.assertEqual(response.status_code, 200)

		self.assertIn(self.document.text, response.body.decode('utf-8'))

		preview_url = '/ws/preview'
		with self.settings(PREVIEW_URL=preview_url):
			self.assertIn(preview_url, response.body.decode('utf-8'))


class TestPermissionOverview(WebTest):
	csrf_checks = False

	def setUp(self):
		self.user = mommy.make(UserProfile, is_superuser=True)
		self.minutes_document = mommy.make(MinutesDocument)
		self.poll = mommy.make(Poll)
		self.information_document = mommy.make(InformationDocument)
		self.group = mommy.make(Group)
		self.minutes_document.set_all_permissions(self.group)
		self.poll.set_all_permissions(self.group)
		self.information_document.set_all_permissions(self.group)

		self.anonymous_group = Group.objects.get(name=settings.ANONYMOUS_GROUP_NAME)
		self.university_network_group = Group.objects.get(name=settings.UNIVERSITY_GROUP_NAME)
		self.student_group = Group.objects.get(name=settings.STUDENT_GROUP_NAME)
		self.staff_group = Group.objects.get(name=settings.STAFF_GROUP_NAME)
		groups = [self.anonymous_group, self.university_network_group, self.student_group, self.staff_group]
		self.documents = [self.minutes_document, self.poll, self.information_document]
		for document in self.documents:
			for group in groups:
				assign_perm(document.view_permission_name, group, document)
			assign_perm(document.edit_permission_name, self.staff_group, document)

	def test_permission_display(self):
		"""
		Test if the permissions are correctly shown in the sidebar
		"""
		icons = [
			"glyphicon-globe permission-icon-view",
			"glyphicon-education permission-icon-view",
			"glyphicon-user permission-icon-view",
			"glyphicon-briefcase permission-icon-edit"
		]
		for document in self.documents:
			response = self.app.get(reverse(document.get_edit_url_name(), args=[self.minutes_document.url_title]), user=self.user)
			for icon in icons:
				self.assertIn(icon, response)

	def test_permission_display_2(self):
		"""
		Test if the permissions are correctly shown in the sidebar
		"""
		for document in self.documents:
			remove_perm(document.view_permission_name, self.anonymous_group, document)
			assign_perm(document.edit_permission_name, self.student_group, document)
			remove_perm(document.edit_permission_name, self.staff_group, document)

		icons = [
			"glyphicon-globe permission-icon-none",
			"glyphicon-education permission-icon-view",
			"glyphicon-user permission-icon-edit",
			"glyphicon-briefcase permission-icon-view"
		]
		for document in self.documents:
			response = self.app.get(reverse(document.get_edit_url_name(), args=[self.minutes_document.url_title]), user=self.user)
			for icon in icons:
				self.assertIn(icon, response)
