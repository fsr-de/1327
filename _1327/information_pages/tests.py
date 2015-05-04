from django.contrib.auth.models import Group
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.db import transaction
from django_webtest import WebTest
from guardian.shortcuts import assign_perm, get_perms_for_model, remove_perm
from guardian.utils import get_anonymous_user
import reversion
from _1327.information_pages.models import InformationDocument

from _1327.user_management.models import UserProfile
from _1327.documents.models import Document


class TestDocument(TestCase):

	def setUp(self):
		self.user = UserProfile.objects.create_user(username="testuser", email="test@test.de", password="top_secret")
		self.user.save()
		

	def test_slugification(self):
		document = InformationDocument(title="titlea", text="text", author=self.user)
		self.assertEqual(document.url_title, '')
		document.save()
		self.assertEqual(document.url_title, "titlea")

		document.title="bla-keks-kekskeks"
		document.save()
		self.assertEqual(document.url_title, "bla-keks-kekskeks")


class TestDocumentWeb(WebTest):

	def setUp(self):
		self.user = UserProfile.objects.create_user(username="testuser", email="test@test.de", password="top_secret")
		self.user.save()

	def test_url_shows_document(self):
		title = "Document title"
		text = "This is the document text."
		author = self.user
		document = InformationDocument(title=title, text=text, author=author)
		document.save()

		assign_perm(InformationDocument.VIEW_PERMISSION_NAME, author, document)
		self.assertTrue(author.has_perm(InformationDocument.VIEW_PERMISSION_NAME, document))

		self.assertTrue(document.get_url(), msg="InformationDocument should return a URL")

		response = self.app.get(document.get_url(), user=author)

		self.assertIn(title.encode("utf-8"), response.body, msg="The displayed page should contain the document's title")


class TestEditor(WebTest):

	csrf_checks = False

	def setUp(self):
		self.user = UserProfile.objects.create_superuser(username="testuser", email="test@test.de", password="top_secret")
		self.user.is_verified = True
		self.user.is_active = True
		self.user.is_admin = True
		self.user.save()

		self.document = InformationDocument(title="title", text="text", author=self.user)
		self.document.save()


	def test_get_editor(self):
		response = self.app.get(reverse('information_pages:edit', args=[self.document.url_title]), status=403)
		self.assertEqual(response.status_code, 403)

		response = self.app.get(reverse('information_pages:edit', args=[self.document.url_title]), user="testuser")
		self.assertEqual(response.status_code, 200)

		form = response.form
		self.assertEqual(form.get('title').value, self.document.title)
		self.assertEqual(form.get('text').value, self.document.text)

		form.set('comment', 'changed title')
		form.set('title', 'new-title')
		response = form.submit('submit')
		self.assertRedirects(response, reverse('information_pages:edit', args=['new-title']))
		
		document = Document.objects.get(url_title='new-title')
		self.assertEqual(document.url_title, 'new-title')

	def test_editor_error(self):
		for string in ['', ' ']:

			response = self.app.get(reverse('information_pages:edit', args=[self.document.url_title]), user="testuser")

			form = response.form
			form.set('title', string)
			response = form.submit('submit')
			self.assertEqual(response.status_code, 200)
			self.assertIn('has-error', str(response.body))

	def test_editor_permissions_for_single_user(self):
		test_user = UserProfile.objects.create_user("testuser2")

		assign_perm(InformationDocument.VIEW_PERMISSION_NAME, test_user, self.document)

		# test that test_user is not allowed to use editor
		response = self.app.get(reverse('information_pages:edit', args=[self.document.url_title]), user="testuser2", status=403)
		self.assertEqual(response.status_code, 403)

		# give that user the necessary permission and check again
		assign_perm('change_informationdocument', test_user, self.document)

		# it should work now
		response = self.app.get(reverse('information_pages:edit', args=[self.document.url_title]), user="testuser2")
		self.assertEqual(response.status_code, 200)

	def test_editor_permissions_for_groups(self):
		test_user = UserProfile.objects.create_user("testuser2")
		test_group = Group.objects.create(name="testgroup")
		test_user.groups.add(test_group)

		assign_perm(InformationDocument.VIEW_PERMISSION_NAME, test_group, self.document)

		# user should not be able to use the editor
		response = self.app.get(reverse('information_pages:edit', args=[self.document.url_title]), user="testuser2", status=403)
		self.assertEqual(response.status_code, 403)

		# add permission to group
		assign_perm('change_informationdocument', test_group, self.document)

		# user should now be able to use the editor
		response = self.app.get(reverse('information_pages:edit', args=[self.document.url_title]), user="testuser2")
		self.assertEqual(response.status_code, 200)



class TestVersions(WebTest):

	csrf_checks = False

	def setUp(self):
		self.user = UserProfile.objects.create_superuser(username="testuser", email="test@test.de", password="top_secret")
		self.user.is_verified = True
		self.user.is_active = True
		self.user.is_admin = True
		self.user.save()

		self.document = InformationDocument(title="title", text="text", author=self.user)
		with transaction.atomic(), reversion.create_revision():
			self.document.save()
			reversion.set_user(self.user)
			reversion.set_comment('test version')

	def test_get_version_page(self):
		response = self.app.get(reverse('information_pages:versions', args=[self.document.url_title]), status=403)
		self.assertEqual(response.status_code, 403)

		response = self.app.get(reverse('information_pages:versions', args=[self.document.url_title]), user=self.user)
		self.assertEqual(response.status_code, 200)

	def test_save_version(self):
		# first get all current versions of the document from the database
		document = Document.objects.get()
		versions = reversion.get_for_object(document)
		self.assertEqual(len(versions), 1)

		# get the editor page and add a new revision
		response = self.app.get(reverse('information_pages:edit', args=[self.document.url_title]), user=self.user)
		self.assertEqual(response.status_code, 200)

		form = response.form
		new_string = self.document.text + "\nHallo Bibi Blocksberg!!"
		form.set('text', new_string)
		form.set('comment', 'hallo Bibi Blocksberg')
		response = form.submit().follow()
		self.assertEqual(response.status_code, 200)

		# check whether number of versions increased
		versions = reversion.get_for_object(self.document)
		self.assertEqual(len(versions), 2)

		# check whether the comment of the version correct
		self.assertEqual(versions[0].revision.comment, 'hallo Bibi Blocksberg')
		self.assertEqual(versions[1].revision.comment, 'test version')


class TestPermissions(WebTest):

	def setUp(self):
		self.user = UserProfile.objects.create_user("testuser")
		self.user.save()

		self.group = Group.objects.create(name="test_group")
		for permission in get_perms_for_model(InformationDocument):
			permission_name = "{}.{}".format(permission.content_type.app_label, permission.codename)
			assign_perm(permission_name, self.group)
		self.group.save()

		document = InformationDocument(title="title", text="text", author=self.user)
		document.save()

	def test_view_permissions_for_logged_in_user(self):
		# check that user is not allowed to see information document
		document = Document.objects.get()

		response = self.app.get(reverse('information_pages:view_information', args=[document.url_title]), user="testuser", status=403)
		self.assertEqual(response.status_code, 403)

		# grant view permission to that user
		assign_perm(InformationDocument.VIEW_PERMISSION_NAME, self.user, document)
		response = self.app.get(reverse('information_pages:view_information', args=[document.url_title]), user="testuser")
		self.assertEqual(response.status_code, 200)
		remove_perm(InformationDocument.VIEW_PERMISSION_NAME, self.user, document)

		# check that user is not allowed to see page anymore
		response = self.app.get(reverse('information_pages:view_information', args=[document.url_title]), user="testuser", status=403)
		self.assertEqual(response.status_code, 403)

		# add user to test group and test that he is now allowed to see that document
		self.user.groups.add(self.group)
		self.user.save()

		response = self.app.get(reverse('information_pages:view_information', args=[document.url_title]), user="testuser")
		self.assertEqual(response.status_code, 200)

	def test_view_permissions_for_anonymous_user(self):
		anonymous_user = get_anonymous_user()
		document = Document.objects.get()

		# check that anonymous user is not allowed to see that document
		response = self.app.get(reverse('information_pages:view_information', args=[document.url_title]), user=anonymous_user, status=403)
		self.assertEqual(response.status_code, 403)

		# allow anonymous users to see that document and test that
		assign_perm(InformationDocument.VIEW_PERMISSION_NAME, anonymous_user, document)

		# it should work now
		response = self.app.get(reverse('information_pages:view_information', args=[document.url_title]), user=anonymous_user)
		self.assertEqual(response.status_code, 200)

		remove_perm(InformationDocument.VIEW_PERMISSION_NAME, anonymous_user, document)

		# check that anonymous user is not allowed to see page anymore
		response = self.app.get(reverse('information_pages:view_information', args=[document.url_title]), user=anonymous_user, status=403)
		self.assertEqual(response.status_code, 403)

		# test the same with group
		anonymous_user.groups.add(self.group)
		anonymous_user.save()

		response = self.app.get(reverse('information_pages:view_information', args=[document.url_title]), user=anonymous_user)
		self.assertEqual(response.status_code, 200)

	def test_create_permissions_for_logged_in_user(self):
		# check that user is not allowed to create an information document
		response = self.app.get(reverse('information_pages:create'), user="testuser", status=403)
		self.assertEqual(response.status_code, 403)

		# grant add and change permission to that user
		assign_perm('information_pages.add_informationdocument', self.user)
		assign_perm('information_pages.change_informationdocument', self.user)

		response = self.app.get(reverse('information_pages:create'), user="testuser")
		self.assertEqual(response.status_code, 200)
		remove_perm('information_pages.add_informationdocument', self.user)
		remove_perm('information_pages.change_informationdocument', self.user)

		# check that user is not allowed to see page anymore
		response = self.app.get(reverse('information_pages:create'), user="testuser", status=403)
		self.assertEqual(response.status_code, 403)

		# add user to test group and test that he is now allowed to create a information document
		self.user.groups.add(self.group)
		self.user.save()

		response = self.app.get(reverse('information_pages:create'), user="testuser")
		self.assertEqual(response.status_code, 200)

	def test_create_permissions_for_anonymous_user(self):
		anonymous_user = get_anonymous_user()

		# check that anonymous user is not allowed to see that document
		response = self.app.get(reverse('information_pages:create'), user=anonymous_user, status=403)
		self.assertEqual(response.status_code, 403)

		# allow anonymous users to see that document and test that
		assign_perm('information_pages.add_informationdocument', anonymous_user)
		assign_perm('information_pages.change_informationdocument', anonymous_user)

		# it should work now
		response = self.app.get(reverse('information_pages:create'), user=anonymous_user)
		self.assertEqual(response.status_code, 200)

		remove_perm('information_pages.add_informationdocument', anonymous_user)
		remove_perm('information_pages.change_informationdocument', anonymous_user)

		# check that anonymous user is not allowed to see page anymore
		response = self.app.get(reverse('information_pages:create'), user=anonymous_user, status=403)
		self.assertEqual(response.status_code, 403)

		# test the same with group
		anonymous_user.groups.add(self.group)
		anonymous_user.save()

		response = self.app.get(reverse('information_pages:create'))
		self.assertEqual(response.status_code, 200)

class TestNewPage(WebTest):

	csrf_checks = False

	def setUp(self):
		self.user = UserProfile.objects.create_superuser(username="testuser", email="test@test.de", password="top_secret")
		self.user.is_verified = True
		self.user.is_active = True
		self.user.is_admin = True
		self.user.save()

	def test_save_new_page(self):
		# get the editor page and save the site
		response = self.app.get(reverse('information_pages:create'), user=self.user)
		self.assertEqual(response.status_code, 200)

		form = response.form
		text = "Hallo Bibi Blocksberg!"
		form.set('text', text)
		form.set('title', text)
		form.set('comment', text)
		response = form.submit().follow()
		self.assertEqual(response.status_code, 200)

		document = InformationDocument.objects.get(title=text)

		# check whether number of versions is correct
		versions = reversion.get_for_object(document)
		self.assertEqual(len(versions), 1)

		# check whether the properties of the new document are correct
		self.assertEqual(document.title, text)
		self.assertEqual(document.text, text)
		self.assertEqual(versions[0].revision.comment, text)

