from django.test import TestCase
from django.core.urlresolvers import reverse

from django_webtest import WebTest

from _1327.main.models import UserProfile
from _1327.information_pages.models import Document


class TestDocument(TestCase):

	def setUp(self):

		self.user = UserProfile.objects.create_user(username="testuser", email="test@test.de", password="top_secret")
		self.user.save()
		

	def test_slugification(self):
		
		document = Document(title="titlea", text="text", type=1, author=self.user)
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

		self.document = Document(title="title", text="text", type=1, author=self.user)
		self.document.save()


	def test_get_editor(self):

		response = self.app.get(reverse('information_pages:edit', args=[self.document.url_title]))
		self.assertEqual(response.status_code, 302)

		response = self.app.get(reverse('information_pages:edit', args=[self.document.url_title]), user="testuser")
		self.assertEqual(response.status_code, 200)

		form = response.form
		self.assertEqual(form.get('title').value, self.document.title)
		self.assertEqual(form.get('text').value, self.document.text)

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




