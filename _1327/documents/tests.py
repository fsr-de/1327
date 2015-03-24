from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse
from django.db import transaction
from django.test import TestCase
from django_webtest import WebTest
from guardian.shortcuts import get_perms_for_model, assign_perm, get_perms, remove_perm
import reversion
from _1327.information_pages.models import InformationDocument

from _1327.user_management.models import UserProfile
from .models import Document


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


class TestUrls(TestCase):

	def test_document_subclasses_override_get_url_method(self):
		for subclass in Document.__subclasses__():
			if hasattr(subclass, "Meta") and hasattr(subclass.Meta, "abstract") and subclass.Meta.abstract:
				# abstract classes do not have to override the get_url method
				continue

			msg = "All non-abstract subclasses of Document should override the get_url method"
			self.assertIsNot(subclass.get_url, Document.get_url, msg=msg)
