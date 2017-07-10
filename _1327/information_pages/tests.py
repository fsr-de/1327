from django.conf import settings
from django.contrib.auth.models import Group
from django.db import transaction
from django.test import TestCase
from django.urls import reverse
from django_webtest import WebTest
from guardian.shortcuts import assign_perm, get_perms_for_model, remove_perm
from guardian.utils import get_anonymous_user
from model_mommy import mommy
from reversion import revisions
from reversion.models import Version

from _1327.documents.models import Document
from _1327.information_pages.models import InformationDocument
from _1327.main.models import MenuItem
from _1327.main.utils import slugify
from _1327.user_management.models import UserProfile


class TestDocument(TestCase):

	@classmethod
	def setUpTestData(cls):
		cls.user = mommy.make(UserProfile)

	def test_slugification(self):
		document = InformationDocument(title="titlea", text="text")
		self.assertEqual(document.url_title, '')
		document.save()
		self.assertEqual(document.url_title, "titlea")

		document.url_title = "bla/KEKS-kekskeks"
		document.save()
		self.assertEqual(document.url_title, "bla/keks-kekskeks")


class TestDocumentWeb(WebTest):

	@classmethod
	def setUpTestData(cls):
		cls.user = mommy.make(UserProfile)

	def test_url_shows_document(self):
		title = "Document title"
		document = mommy.make(InformationDocument, title=title)

		assign_perm(InformationDocument.VIEW_PERMISSION_NAME, self.user, document)
		self.assertTrue(self.user.has_perm(InformationDocument.VIEW_PERMISSION_NAME, document))

		self.assertTrue(document.get_view_url(), msg="InformationDocument should return a URL")

		response = self.app.get(document.get_view_url(), user=self.user)

		self.assertIn(title.encode("utf-8"), response.body, msg="The displayed page should contain the document's title")


class TestEditor(WebTest):
	csrf_checks = False
	extra_environ = {'HTTP_ACCEPT_LANGUAGE': 'en'}

	@classmethod
	def setUpTestData(cls):
		cls.user = mommy.make(UserProfile, is_superuser=True)
		cls.user.groups.add(Group.objects.get(name=settings.STAFF_GROUP_NAME))
		cls.document = mommy.make(InformationDocument)
		cls.document.set_all_permissions(mommy.make(Group))

	def test_get_editor(self):
		user_without_perms = mommy.make(UserProfile)
		response = self.app.get(
			reverse(self.document.get_edit_url_name(), args=[self.document.url_title]),
			status=403,
			user=user_without_perms
		)
		self.assertEqual(response.status_code, 403)

		response = self.app.get(reverse(self.document.get_edit_url_name(), args=[self.document.url_title]), user=self.user)
		self.assertEqual(response.status_code, 200)

		form = response.forms[0]
		self.assertEqual(form.get('title').value, self.document.title)
		self.assertEqual(form.get('text').value, self.document.text)

		self.assertTrue("Hidden" in str(form.fields['group'][0]))

		form.set('comment', 'changed title')
		form.set('title', 'new-title')
		form.set('url_title', 'new-url-title')
		response = form.submit('submit')
		self.assertRedirects(response, reverse(self.document.get_view_url_name(), args=['new-url-title']))

		document = Document.objects.get(url_title='new-url-title')
		self.assertEqual(document.url_title, 'new-url-title')

	def test_editor_error(self):
		for string in ['', ' ']:
			response = self.app.get(reverse(self.document.get_edit_url_name(), args=[self.document.url_title]), user=self.user)

			form = response.forms[0]
			form.set('title', string)
			response = form.submit()
			self.assertEqual(response.status_code, 200)
			self.assertIn('has-error', str(response.body))

	def test_editor_slug_error(self):
		response = self.app.get(reverse(self.document.get_edit_url_name(), args=[self.document.url_title]), user=self.user)

		form = response.forms[0]
		form.set('url_title', 'not_ALLOWED!')
		response = form.submit()
		self.assertEqual(response.status_code, 200)
		self.assertIn('has-error', str(response.body))
		self.assertIn('Only the following characters are allowed in the URL', str(response.body))

	def test_editor_permissions_for_single_user(self):
		test_user = mommy.make(UserProfile)
		test_user.groups.add(Group.objects.get(name=settings.STAFF_GROUP_NAME))

		assign_perm(InformationDocument.VIEW_PERMISSION_NAME, test_user, self.document)

		# test that test_user is not allowed to use editor
		response = self.app.get(reverse(self.document.get_edit_url_name(), args=[self.document.url_title]), user=test_user, status=403)
		self.assertEqual(response.status_code, 403)

		# give that user the necessary permission and check again
		assign_perm('change_informationdocument', test_user, self.document)

		# it should work now
		response = self.app.get(reverse(self.document.get_edit_url_name(), args=[self.document.url_title]), user=test_user)
		self.assertEqual(response.status_code, 200)

	def test_editor_permissions_for_groups(self):
		test_user = mommy.make(UserProfile)
		test_group = mommy.make(Group)
		test_user.groups.add(test_group)

		assign_perm(InformationDocument.VIEW_PERMISSION_NAME, test_group, self.document)

		# user should not be able to use the editor
		response = self.app.get(reverse(self.document.get_edit_url_name(), args=[self.document.url_title]), user=test_user, status=403)
		self.assertEqual(response.status_code, 403)

		# add permission to group
		assign_perm('change_informationdocument', test_group, self.document)

		# user should now be able to use the editor
		response = self.app.get(reverse(self.document.get_edit_url_name(), args=[self.document.url_title]), user=test_user)
		self.assertEqual(response.status_code, 200)


class TestVersions(WebTest):
	csrf_checks = False

	@classmethod
	def setUpTestData(cls):
		cls.user = mommy.make(UserProfile, is_superuser=True)
		cls.user.groups.add(Group.objects.get(name=settings.STAFF_GROUP_NAME))

		cls.document = mommy.prepare(InformationDocument)
		with transaction.atomic(), revisions.create_revision():
			cls.document.save()
			revisions.set_user(cls.user)
			revisions.set_comment('test version')
		cls.document.set_all_permissions(mommy.make(Group))

	def test_get_version_page(self):
		user_without_perms = mommy.make(UserProfile)
		response = self.app.get(
			reverse(self.document.get_versions_url_name(), args=[self.document.url_title]),
			status=403,
			user=user_without_perms
		)
		self.assertEqual(response.status_code, 403)

		response = self.app.get(reverse(self.document.get_versions_url_name(), args=[self.document.url_title]), user=self.user)
		self.assertEqual(response.status_code, 200)

	def test_save_version(self):
		# first get all current versions of the document from the database
		versions = Version.objects.get_for_object(self.document)
		self.assertEqual(len(versions), 1)

		# get the editor page and add a new revision
		response = self.app.get(reverse(self.document.get_edit_url_name(), args=[self.document.url_title]), user=self.user)
		self.assertEqual(response.status_code, 200)

		form = response.forms[0]
		new_string = self.document.text + "\nHallo Bibi Blocksberg!!"
		form.set('text', new_string)
		form.set('comment', 'hallo Bibi Blocksberg')
		form.set('url_title', 'bibi-blocksberg')
		response = form.submit().follow()
		self.assertEqual(response.status_code, 200)

		# check whether number of versions increased
		versions = Version.objects.get_for_object(self.document)
		self.assertEqual(len(versions), 2)

		# check whether the comment of the version correct
		self.assertEqual(versions[0].revision.comment, 'hallo Bibi Blocksberg')
		self.assertEqual(versions[1].revision.comment, 'test version')


class TestPermissions(WebTest):

	@classmethod
	def setUpTestData(cls):
		cls.user = mommy.make(UserProfile)
		cls.user.groups.add(Group.objects.get(name=settings.STAFF_GROUP_NAME))

		cls.group = mommy.make(Group, make_m2m=True)
		for permission in get_perms_for_model(InformationDocument):
			permission_name = "{}.{}".format(permission.content_type.app_label, permission.codename)
			assign_perm(permission_name, cls.group)
		cls.group.save()

		mommy.make(InformationDocument)

	def test_view_permissions_for_logged_in_user(self):
		# check that user is not allowed to see information document
		document = Document.objects.get()

		response = self.app.get(reverse(document.get_view_url_name(), args=[document.url_title]) + '/', user=self.user)
		self.assertEqual(response.status_code, 301)

		response = self.app.get(reverse(document.get_view_url_name(), args=[document.url_title]), user=self.user, status=403)
		self.assertEqual(response.status_code, 403)

		# grant view permission to that user
		assign_perm(InformationDocument.VIEW_PERMISSION_NAME, self.user, document)
		response = self.app.get(reverse(document.get_view_url_name(), args=[document.url_title]) + '/', user=self.user)
		self.assertEqual(response.status_code, 301)

		response = self.app.get(reverse(document.get_view_url_name(), args=[document.url_title]), user=self.user)
		self.assertEqual(response.status_code, 200)
		remove_perm(InformationDocument.VIEW_PERMISSION_NAME, self.user, document)

		# check that user is not allowed to see page anymore
		response = self.app.get(reverse(document.get_view_url_name(), args=[document.url_title]) + '/', user=self.user)
		self.assertEqual(response.status_code, 301)

		response = self.app.get(reverse(document.get_view_url_name(), args=[document.url_title]), user=self.user, status=403)
		self.assertEqual(response.status_code, 403)

		# add user to test group and test that he is now allowed to see that document
		self.user.groups.add(self.group)
		self.user.save()

		response = self.app.get(reverse(document.get_view_url_name(), args=[document.url_title]), user=self.user)
		self.assertEqual(response.status_code, 200)

	def test_view_permissions_for_anonymous_user(self):
		anonymous_user = get_anonymous_user()
		document = Document.objects.get()

		# check that anonymous user is not allowed to see that document
		response = self.app.get(reverse(document.get_view_url_name(), args=[document.url_title]), user=anonymous_user, status=403)
		self.assertEqual(response.status_code, 403)

		# allow anonymous users to see that document and test that
		assign_perm(InformationDocument.VIEW_PERMISSION_NAME, anonymous_user, document)

		# it should work now
		response = self.app.get(reverse(document.get_view_url_name(), args=[document.url_title]), user=anonymous_user)
		self.assertEqual(response.status_code, 200)

		remove_perm(InformationDocument.VIEW_PERMISSION_NAME, anonymous_user, document)

		# check that anonymous user is not allowed to see page anymore
		response = self.app.get(reverse(document.get_view_url_name(), args=[document.url_title]), user=anonymous_user, status=403)
		self.assertEqual(response.status_code, 403)

		# test the same with group
		anonymous_user.groups.add(self.group)
		anonymous_user.save()

		response = self.app.get(reverse(document.get_view_url_name(), args=[document.url_title]), user=anonymous_user)
		self.assertEqual(response.status_code, 200)

	def test_create_permissions_for_logged_in_user(self):
		# check that user is not allowed to create an information document
		response = self.app.get(reverse('documents:create', args=['informationdocument']), user=self.user, status=403)
		self.assertEqual(response.status_code, 403)

		# grant add and change permission to that user
		assign_perm('information_pages.add_informationdocument', self.user)
		assign_perm('information_pages.change_informationdocument', self.user)

		response = self.app.get(reverse('documents:create', args=['informationdocument']), user=self.user)
		self.assertEqual(response.status_code, 200)
		remove_perm('information_pages.add_informationdocument', self.user)
		remove_perm('information_pages.change_informationdocument', self.user)

		# check that user is not allowed to see page anymore
		response = self.app.get(reverse('documents:create', args=['informationdocument']), user=self.user, status=403)
		self.assertEqual(response.status_code, 403)

		# add user to test group and test that he is now allowed to create a information document
		self.user.groups.add(self.group)
		self.user.save()

		response = self.app.get(reverse('documents:create', args=['informationdocument']), user=self.user)
		self.assertEqual(response.status_code, 200)

	def test_create_permissions_for_anonymous_user(self):
		anonymous_user = get_anonymous_user()

		# check that anonymous user is not allowed to see that document
		response = self.app.get(reverse('documents:create', args=['informationdocument']), user=anonymous_user, status=403)
		self.assertEqual(response.status_code, 403)

		# allow anonymous users to see that document and test that
		assign_perm('information_pages.add_informationdocument', anonymous_user)
		assign_perm('information_pages.change_informationdocument', anonymous_user)

		# it should still not work
		response = self.app.get(reverse('documents:create', args=['informationdocument']), user=anonymous_user, status=403)
		self.assertEqual(response.status_code, 403)

		# the user also needs to be in a group that allows him to create documents
		anonymous_user.groups.add(Group.objects.get(name=settings.STAFF_GROUP_NAME))

		# it should work now
		response = self.app.get(reverse('documents:create', args=['informationdocument']), user=anonymous_user)
		self.assertEqual(response.status_code, 200)

		anonymous_user.groups.remove(Group.objects.get(name=settings.STAFF_GROUP_NAME))
		remove_perm('information_pages.add_informationdocument', anonymous_user)
		remove_perm('information_pages.change_informationdocument', anonymous_user)

		# check that anonymous user is not allowed to see page anymore
		response = self.app.get(reverse('documents:create', args=['informationdocument']), user=anonymous_user, status=403)
		self.assertEqual(response.status_code, 403)

		# test the same with group
		anonymous_user.groups.add(self.group)
		anonymous_user.save()

		response = self.app.get(reverse('documents:create', args=['informationdocument']))
		self.assertEqual(response.status_code, 200)


class TestNewPage(WebTest):
	csrf_checks = False

	@classmethod
	def setUpTestData(cls):
		cls.user = mommy.make(UserProfile, is_superuser=True)

	def test_save_new_page(self):
		# get the editor page and save the site
		group = mommy.make(Group)
		group.user_set.add(self.user)
		response = self.app.get(reverse('documents:create', args=['informationdocument']), user=self.user)
		self.assertEqual(response.status_code, 200)

		form = response.forms[0]
		text = "Hallo Bibi Blocksberg!"
		form.set('text', text)
		form.set('title', text)
		form.set('comment', text)
		form.set('url_title', slugify(text))
		form.set('group', group.pk)

		response = form.submit().follow()
		self.assertEqual(response.status_code, 200)

		document = InformationDocument.objects.get(title=text)

		# check whether number of versions is correct
		versions = Version.objects.get_for_object(document)
		self.assertEqual(len(versions), 1)

		# check whether the properties of the new document are correct
		self.assertEqual(document.title, text)
		self.assertEqual(document.text, text)
		self.assertEqual(versions[0].revision.comment, text)

	def test_save_new_page_with_slash_url(self):
		# get the editor page and save the site
		group = mommy.make(Group)
		group.user_set.add(self.user)
		response = self.app.get(reverse('documents:create', args=['informationdocument']), user=self.user)
		self.assertEqual(response.status_code, 200)

		form = response.forms[0]
		text = "Lorem ipsum"
		url = "some/page-with-slash"
		form.set('text', text)
		form.set('title', text)
		form.set('comment', text)
		form.set('url_title', url)
		form.set('group', group.pk)

		response = form.submit().follow()
		self.assertEqual(response.status_code, 200)

		document = InformationDocument.objects.get(title=text)
		self.assertEqual(document.url_title, url)

		response = self.app.get('/' + url + '/', user=self.user)
		self.assertEqual(response.status_code, 301)

		response = self.app.get('/' + url, user=self.user)
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'documents_base.html')

		response = self.app.get('/' + url + '/edit/', user=self.user)
		self.assertEqual(response.status_code, 301)

		response = self.app.get('/' + url + '/edit', user=self.user)
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'documents_edit.html')

	def test_group_field_hidden_when_user_has_one_group(self):
		group = mommy.make(Group)
		self.user.groups.add(group)
		response = self.app.get(reverse('documents:create', args=['informationdocument']), user=self.user)
		self.assertEqual(response.status_code, 200)

		form = response.forms[0]
		self.assertTrue("Hidden" in str(form.fields['group'][0]))

	def test_group_field_not_hidden_when_user_has_multiple_groups(self):
		groups = mommy.make(Group, _quantity=2)
		self.user.groups.add(*groups)
		response = self.app.get(reverse('documents:create', args=['informationdocument']), user=self.user)
		self.assertEqual(response.status_code, 200)

		form = response.forms[0]
		self.assertFalse("Hidden" in str(form.fields['group'][0]))


class TestUnlinkedList(WebTest):

	@classmethod
	def setUpTestData(cls):
		cls.user = mommy.make(UserProfile, is_superuser=True)
		cls.informationdocument1 = mommy.make(InformationDocument)
		cls.informationdocument2 = mommy.make(InformationDocument, text="Lorem ipsum [link](document:{}).".format(cls.informationdocument1.id))
		cls.menu_item = mommy.make(MenuItem, document=cls.informationdocument2)

	def test_url_shows_document(self):
		self.assertTrue(self.informationdocument2.menu_items.count() > 0)
		self.assertEqual(self.informationdocument1.menu_items.count(), 0)

		response = self.app.get(reverse('information_pages:unlinked_list'), user=self.user)
		self.assertIn(self.informationdocument1.title.encode("utf-8"), response.body, msg="The displayed page should contain the unlinked document's title")

		self.informationdocument2.is_menu_page = True
		self.informationdocument2.save()

		response = self.app.get(reverse('information_pages:unlinked_list'), user=self.user)
		self.assertNotIn(self.informationdocument1.title.encode("utf-8"), response.body, msg="The displayed page should not contain the document's title")
