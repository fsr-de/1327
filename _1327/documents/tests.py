import tempfile
from django.contrib.auth.models import Group
from django.core.files.base import ContentFile
from django.core.urlresolvers import reverse
from django.db import transaction
from django.test import TestCase
from django_webtest import WebTest
from guardian.shortcuts import get_perms_for_model, assign_perm, get_perms, remove_perm
import reversion
from _1327.information_pages.models import InformationDocument

from _1327.user_management.models import UserProfile
from .models import Document, Attachment


class TestRevertion(WebTest):

	csrf_checks = False

	def setUp(self):
		self.user = UserProfile.objects.create_superuser('test', 'test', 'test@test.test', 'test', 'test')
		self.user.is_active = True
		self.user.is_verified = True
		self.user.is_admin = True
		self.user.save()

		document = Document(title="title", text="text", author=self.user)
		with transaction.atomic(), reversion.create_revision():
				document.save()
				reversion.set_user(self.user)
				reversion.set_comment('test version')

		# create a second version
		document.text += '\nmore text'
		with transaction.atomic(), reversion.create_revision():
				document.save()
				reversion.set_user(self.user)
				reversion.set_comment('added more text')

	def test_only_admin_may_revert(self):
		document = Document.objects.get()
		versions = reversion.get_for_object(document)
		self.assertEqual(len(versions), 2)

		response = self.app.post(reverse('documents:revert'), {'id': versions[1].pk, 'url_title': document.url_title}, status=404)
		self.assertEqual(response.status_code, 404)

		response = self.app.post(reverse('documents:revert'), {'id': versions[1].pk, 'url_title': document.url_title}, status=403, xhr=True)
		self.assertEqual(response.status_code, 403)

		response = self.app.post(reverse('documents:revert'), {'id': versions[1].pk, 'url_title': document.url_title}, user=self.user, status=404)
		self.assertEqual(response.status_code, 404)

		response = self.app.post(reverse('documents:revert'), {'id': versions[1].pk, 'url_title': document.url_title}, user=self.user, xhr=True)
		self.assertEqual(response.status_code, 200)

	def test_revert_document(self):
		document = Document.objects.get()
		versions = reversion.get_for_object(document)
		self.assertEqual(len(versions), 2)

		# second step try to revert to old version
		response = self.app.post(reverse('documents:revert'), {'id': versions[1].pk, 'url_title': document.url_title}, user=self.user, xhr=True)
		self.assertEqual(response.status_code, 200)

		versions = reversion.get_for_object(document)
		self.assertEqual(len(versions), 3)
		self.assertEqual(versions[0].object.text, "text")
		self.assertEqual(versions[0].revision.comment, 'reverted to revision "test version"')

class TestAutosave(WebTest):

	csrf_checks = False

	def setUp(self):
		self.user = UserProfile.objects.create_superuser('test', 'test', 'test@test.test', 'test', 'test')
		self.user.is_active = True
		self.user.is_verified = True
		self.user.is_admin = True
		self.user.save()

		document = InformationDocument(title="title", text="text", author=self.user)
		with transaction.atomic(), reversion.create_revision():
				document.save()
				reversion.set_user(self.user)
				reversion.set_comment('test version')

	def test_autosave(self):
		# get document
		document = Document.objects.get()

		# document text should be text
		response = self.app.get(reverse('information_pages:edit', args=[document.url_title]), user=self.user)
		self.assertEqual(response.status_code, 200)
		form = response.form
		self.assertEqual(form.get('text').value, 'text')

		# autosave AUTO
		response = self.app.post(reverse('information_pages:autosave', args=[document.url_title]), {'text': 'AUTO', 'title': form.get('title').value, 'comment': ''}, user=self.user, xhr=True)
		self.assertEqual(response.status_code, 200)

		# if not loading autosave text should be still text
		response = self.app.get(reverse('information_pages:edit', args=[document.url_title]), user=self.user)
		self.assertEqual(response.status_code, 200)
		form = response.form
		self.assertEqual(form.get('text').value, 'text')

		# if loading autosave text should be AUTO
		response = self.app.get(reverse('information_pages:edit', args=[document.url_title]), {'restore' : ''}, user=self.user)
		self.assertEqual(response.status_code, 200)
		form = response.form
		self.assertEqual(form.get('text').value, 'AUTO')

		# second autosave AUTO2
		response = self.app.post(reverse('information_pages:autosave', args=[document.url_title]), {'text': 'AUTO2', 'title': form.get('title').value, 'comment' : ''}, user=self.user, xhr=True)
		self.assertEqual(response.status_code, 200)

		# if loading autosave text should be AUTO2
		response = self.app.get(reverse('information_pages:edit', args=[document.url_title]), {'restore' : ''}, user=self.user)
		self.assertEqual(response.status_code, 200)
		form = response.form
		self.assertEqual(form.get('text').value, 'AUTO2')


class TestSignals(TestCase):

	def setUp(self):
		self.user = UserProfile.objects.create_superuser('test', 'test', 'test@test.test', 'test', 'test')
		self.user.save()

	def test_slugify_hook(self):
		# create a new document for every subclass of document
		# and see whether the url_title is automatically created
		for obj_id, subclass in enumerate(Document.__subclasses__()):
			new_document = subclass.objects.create(title="test_{}".format(obj_id), author=self.user)
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
			test_object = subclass.objects.create(title="test", author=self.user)
			user_permissions = get_perms(group, test_object)
			self.assertNotEqual(len(user_permissions), 0)

			for permission in group.permissions.all():
				self.assertIn(permission.codename, user_permissions)

	def test_possibility_to_change_permission_for_groups(self):
		group = Group.objects.create(name="FSR")
		test_user = UserProfile.objects.create_user("test2", "test")
		test_user.groups.add(group)
		test_user.save()

		model_permissions = get_perms_for_model(InformationDocument)
		for permission in model_permissions:
			permission_name = "{}.{}".format(permission.content_type.app_label, permission.codename)
			assign_perm(permission_name, group)

		# test whether we can remove a permission from the group
		# the permission should not be added again
		test_object = InformationDocument.objects.create(title="test", author=self.user)
		self.assertTrue(test_user.has_perm(model_permissions[0].codename, test_object))
		remove_perm(model_permissions[0].codename, group, test_object)
		test_object.save()
		self.assertFalse(test_user.has_perm(model_permissions[0].codename, test_object))


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
			self.assertIsNot(subclass.get_url, Document.get_url, msg=msg)

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
		self.user = UserProfile.objects.create_superuser("test", "test", "test@test.test")

		self.group = Group.objects.create(name="testgroup")
		for permission in get_perms_for_model(InformationDocument):
			permission_name = "{}.{}".format(permission.content_type.app_label, permission.codename)
			assign_perm(permission_name, self.group)
		self.group.save()

		self.group_user = UserProfile.objects.create_user("groupuser", "test", "test@test.test")
		self.group_user.groups.add(self.group)
		self.group_user.save()

		self.document = InformationDocument(author=self.user, title="test", text="blabla")
		self.document.save()

		self.content = "test content of test attachment"
		attachment_file = ContentFile(self.content)
		self.attachment = Attachment.objects.create(document=self.document)
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
		normal_user = UserProfile.objects.create_user("normal", "test", "normal@test.test")

		response = self.app.get(reverse('information_pages:attachments', args=[self.document.url_title]),
									user=normal_user,
									expect_errors=True)
		self.assertEqual(response.status_code, 403)

		response = self.app.post(reverse('information_pages:attachments', args=[self.document.url_title]),
									content_type='multipart/form-data',
									upload_files=upload_files,
									user=normal_user,
									expect_errors=True)
		self.assertEqual(response.status_code, 403)

		# test that user who is allowed to view the document may not add attachments to it
		# and neither see the corresponding page
		assign_perm("view_informationdocument", normal_user, self.document)

		response = self.app.get(reverse('information_pages:attachments', args=[self.document.url_title]),
									user=normal_user,
									expect_errors=True)
		self.assertEqual(response.status_code, 403)

		response = self.app.post(reverse('information_pages:attachments', args=[self.document.url_title]),
									content_type='multipart/form-data',
									upload_files=upload_files,
									user=normal_user,
									expect_errors=True)
		self.assertEqual(response.status_code, 403)

		# test that member of group who has according permissions is allowed to upload attachments
		# and to see the corresponding page
		response = self.app.get(reverse('information_pages:attachments', args=[self.document.url_title]),
									user=self.group_user)
		self.assertEqual(response.status_code, 200)

		response = self.app.post(reverse('information_pages:attachments', args=[self.document.url_title]),
									content_type='multipart/form-data',
									upload_files=upload_files,
									user=self.group_user)
		self.assertEqual(response.status_code, 200)

		# test that superuser is allowed to upload attachments and to see the corresponding page
		response = self.app.get(reverse('information_pages:attachments', args=[self.document.url_title]),
									user=self.user)
		self.assertEqual(response.status_code, 200)

		response = self.app.post(reverse('information_pages:attachments', args=[self.document.url_title]),
									content_type='multipart/form-data',
									upload_files=upload_files,
									user=self.user)
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
		self.assertEqual(response.status_code, 403,
						msg="If users have no permissions they should not be able to delete an attachment")

		# try to delete an attachment as user with no permissions
		normal_user = UserProfile.objects.create_user("normal", "test", "normal@test.test")
		response = self.app.post(reverse('documents:delete_attachment'), params=params, expect_errors=True, xhr=True,
								user=normal_user)
		self.assertEqual(response.status_code, 403,
						msg="If users have no permissions they should not be able to delete an attachment")

		# try to delete an attachment as user with wrong permissions
		assign_perm(InformationDocument.get_view_permission(), normal_user, self.document)
		response = self.app.post(reverse('documents:delete_attachment'), params=params, expect_errors=True, xhr=True,
								user=normal_user)
		self.assertEqual(response.status_code, 403,
						msg="If users has no permissions they should not be able to delete an attachment")

		# try to delete an attachment as user with correct permissions
		response = self.app.post(reverse('documents:delete_attachment'), params=params, xhr=True,
								user=self.group_user)
		self.assertEqual(response.status_code, 200,
						msg="Users with the correct permissions for a document should be able to delete an attachment")

		# re create the attachment
		self.attachment.save()

		# try to delete an attachment as superuser
		response = self.app.post(reverse('documents:delete_attachment'), params=params, xhr=True,
								user=self.user)
		self.assertEqual(response.status_code, 200,
						msg="Users with the correct permissions for a document should be able to delete an attachment")

	def test_view_attachment(self):
		params = {
			'attachment_id': self.attachment.id,
		}

		# test that a user with insufficient permissions is not allowed to view/download an attachment
		# be an anonymous user
		response = self.app.post(reverse('documents:download_attachment'), params=params, expect_errors=True)
		self.assertEqual(response.status_code, 400, msg="Should be bad request as user used wrong request method")

		response = self.app.get(reverse('documents:download_attachment'), params=params, expect_errors=True)
		self.assertEqual(response.status_code, 403, msg="Should be forbidden as user has insufficient permissions")

		# test viewing an attachment using a user with insufficient permissions
		normal_user = UserProfile.objects.create_user("normal", "test", "normal@test.test")
		assign_perm('change_informationdocument', normal_user, self.document)

		response = self.app.get(reverse('documents:download_attachment'), params=params, expect_errors=True,
								user=normal_user)
		self.assertEqual(response.status_code, 403, msg="Should be forbidden as user has insufficient permissions")

		# grant the correct permission to the user an try again
		assign_perm(InformationDocument.get_view_permission(), normal_user, self.document)

		response = self.app.get(reverse('documents:download_attachment'), params=params, user=normal_user)
		self.assertEqual(response.status_code, 200,
						msg="Users with sufficient permissions should be able to download an attachment")
		self.assertEqual(response.body.decode('utf-8'), self.content,
						msg="An attachment that has been downloaded should contain its original content")

		# try the same with a user that is in a group having the correct permission
		response = self.app.get(reverse('documents:download_attachment'), params=params, user=self.group_user)
		self.assertEqual(response.status_code, 200,
						msg="Users with sufficient permissions should be able to download an attachment")
		self.assertEqual(response.body.decode('utf-8'), self.content,
						msg="An attachment that has been downloaded should contain its original content")

		# make sure that a superuser is always allowed to download an attachment
		response = self.app.get(reverse('documents:download_attachment'), params=params, user=self.user)
		self.assertEqual(response.status_code, 200,
						msg="Users with sufficient permissions should be able to download an attachment")
		self.assertEqual(response.body.decode('utf-8'), self.content,
						msg="An attachment that has been downloaded should contain its original content")
