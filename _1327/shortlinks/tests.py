from django.test import TestCase
from django_webtest import WebTest
from guardian.shortcuts import assign_perm
from model_mommy import mommy

from _1327.information_pages.models import InformationDocument
from _1327.user_management.models import UserProfile
from .models import Shortlink


class TestShortlink(TestCase):

	def test_slugification(self):
		shortlink = Shortlink(url_title="test", link="https://example.com")
		shortlink.save()
		self.assertEqual(shortlink.url_title, "test")

		shortlink.url_title = "etc//TEST-testtest/"
		shortlink.save()
		self.assertEqual(shortlink.url_title, "etc/test-testtest")


class TestShortlinkWeb(WebTest):

	@classmethod
	def setUpTestData(cls):
		cls.user = mommy.make(UserProfile)
		cls.document = mommy.make(InformationDocument, text="Internal shortlink example")
		assign_perm(InformationDocument.VIEW_PERMISSION_NAME, cls.user, cls.document)

	def test_follow_shortlink_external(self):
		url = "https://github.com"
		shortlink = Shortlink(url_title="test", link=url)
		shortlink.save()

		self.assertEqual(shortlink.visit_count, 0)

		response = self.app.get("/test", user=self.user)
		self.assertEqual(response.status_code, 302)
		self.assertEqual(response.location, url)

		shortlink = Shortlink.objects.get(url_title="test")
		self.assertEqual(shortlink.visit_count, 1)

	def test_follow_shortlink_internal(self):
		shortlink = Shortlink(url_title="test", document=self.document)
		shortlink.save()

		self.assertEqual(shortlink.visit_count, 0)

		response = self.app.get("/test", user=self.user)
		self.assertEqual(response.status_code, 302)
		response = response.follow()
		self.assertEqual(response.status_code, 200)
		self.assertIn(self.document.text.encode("utf-8"), response.body)

		shortlink = Shortlink.objects.get(url_title="test")
		self.assertEqual(shortlink.visit_count, 1)
