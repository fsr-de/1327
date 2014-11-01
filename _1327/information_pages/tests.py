from django.test import TestCase
from django.core.urlresolvers import reverse
from django.db import transaction
from django_webtest import WebTest
import reversion

from _1327.main.models import UserProfile
from _1327.documents.models import Document


class TestDocument(TestCase):

	def setUp(self):
		self.user = UserProfile.objects.create_user(username="testuser", email="test@test.de", password="top_secret")
		self.user.save()
		

	def test_slugification(self):
		document = Document(title="titlea", text="text", type='I', author=self.user)
		self.assertEqual(document.url_title, '')
		document.save()
		self.assertEqual(document.url_title, "titlea")

		document.title="bla-keks-kekskeks"
		document.save()
		self.assertEqual(document.url_title, "bla-keks-kekskeks")

class TestEditor(WebTest):

	csrf_checks = False

	def setUp(self):
		self.user = UserProfile.objects.create_superuser(username="testuser", email="test@test.de", password="top_secret")
		self.user.is_verified = True
		self.user.is_active = True
		self.user.is_admin = True
		self.user.save()

		self.document = Document(title="title", text="text", type='I', author=self.user)
		self.document.save()


	def test_get_editor(self):
		response = self.app.get(reverse('information_pages:edit', args=[self.document.url_title]))
		self.assertEqual(response.status_code, 302)

		response = self.app.get(reverse('information_pages:edit', args=[self.document.url_title]), user="testuser")
		self.assertEqual(response.status_code, 200)

		form = response.form
		self.assertEqual(form.get('title').value, self.document.title)
		self.assertEqual(form.get('text').value, self.document.text)

		form.set('comment', 'changed title')
		form.set('title', 'new-title')
		form.submit('submit')


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


class TestVersions(WebTest):

	csrf_checks = False

	def setUp(self):
		self.user = UserProfile.objects.create_superuser(username="testuser", email="test@test.de", password="top_secret")
		self.user.is_verified = True
		self.user.is_active = True
		self.user.is_admin = True
		self.user.save()

		self.document = Document(title="title", text="text", type='I', author=self.user)
		with transaction.atomic(), reversion.create_revision():
			self.document.save()
			reversion.set_user(self.user)
			reversion.set_comment('test version')

	def test_get_version_page(self):
		response = self.app.get(reverse('information_pages:versions', args=[self.document.url_title]))
		self.assertEqual(response.status_code, 302)

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
