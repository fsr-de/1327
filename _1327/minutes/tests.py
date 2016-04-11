from django.conf import settings
from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse
from django_webtest import WebTest
from guardian.core import ObjectPermissionChecker
from guardian.shortcuts import assign_perm, remove_perm
from model_mommy import mommy

from _1327.minutes.models import MinutesDocument
from _1327.user_management.models import UserProfile


class TestEditor(WebTest):
	csrf_checks = False

	def setUp(self):
		num_participants = 8

		self.user = mommy.make(UserProfile, is_superuser=True)
		self.moderator = mommy.make(UserProfile)
		self.participants = mommy.make(UserProfile, _quantity=num_participants)
		self.document = mommy.make(MinutesDocument, participants=self.participants, moderator=self.moderator)

	def test_get_editor(self):
		"""
		Test if the edit page shows the correct content
		"""
		response = self.app.get(reverse('documents:edit', args=[self.document.url_title]), expect_errors=True)
		self.assertEqual(response.status_code, 403)  # test anonymous user cannot access page

		response = self.app.get(reverse('documents:edit', args=[self.document.url_title]), user=self.user)
		self.assertEqual(response.status_code, 200)

		form = response.forms[0]
		self.assertEqual(form.get('title').value, self.document.title)
		self.assertEqual(form.get('text').value, self.document.text)
		self.assertEqual(int(form.get('moderator').value), self.document.moderator.id)
		self.assertEqual([int(id) for id in form.get('participants').value], [participant.id for participant in self.document.participants.all()])

	def test_publish_permission_button_displayed(self):
		"""
		Test if the publish and permission buttons are displayed on the correct minutes states
		"""
		unpublished_document = mommy.make(MinutesDocument, participants=self.participants, moderator=self.moderator, state=MinutesDocument.UNPUBLISHED)
		response = self.app.get(reverse('documents:view', args=[unpublished_document.url_title]), user=self.user)
		self.assertIn("Publish", response)
		self.assertNotIn("Berechtigungen", response)  # this is localized on the build server

		published_document = mommy.make(MinutesDocument, participants=self.participants, moderator=self.moderator, state=MinutesDocument.PUBLISHED)
		response = self.app.get(reverse('documents:view', args=[published_document.url_title]), user=self.user)
		self.assertNotIn("Publish", response)
		self.assertNotIn("Berechtigungen", response)  # this is localized on the build server

		internal_document = mommy.make(MinutesDocument, participants=self.participants, moderator=self.moderator, state=MinutesDocument.INTERNAL)
		response = self.app.get(reverse('documents:view', args=[internal_document.url_title]), user=self.user)
		self.assertNotIn("Publish", response)
		self.assertNotIn("Berechtigungen", response)  # this is localized on the build server

		custom_document = mommy.make(MinutesDocument, participants=self.participants, moderator=self.moderator, state=MinutesDocument.CUSTOM)
		response = self.app.get(reverse('documents:view', args=[custom_document.url_title]), user=self.user)
		self.assertNotIn("Publish", response)
		self.assertIn("Berechtigungen", response)  # this is localized on the build server

	def test_publish_button(self):
		"""
		Test if the publish button works
		"""
		document = mommy.make(MinutesDocument, participants=self.participants, moderator=self.moderator, state=MinutesDocument.UNPUBLISHED)
		self.app.get(reverse('documents:publish', args=[document.url_title]), user=self.user)

		document = MinutesDocument.objects.get(url_title=document.url_title)
		self.assertEqual(document.state, MinutesDocument.PUBLISHED)

		group = Group.objects.get(name=settings.UNIVERSITY_GROUP_NAME)
		checker = ObjectPermissionChecker(group)
		self.assertTrue(checker.has_perm(document.view_permission_name, document))
		self.assertFalse(checker.has_perm(document.edit_permission_name, document))
		self.assertFalse(checker.has_perm(document.delete_permission_name, document))

		group = Group.objects.get(name=settings.STAFF_GROUP_NAME)
		checker = ObjectPermissionChecker(group)
		self.assertTrue(checker.has_perm(document.view_permission_name, document))
		self.assertTrue(checker.has_perm(document.edit_permission_name, document))
		self.assertTrue(checker.has_perm(document.delete_permission_name, document))

	def test_state_permission_update(self):
		"""
		Test if the permission are correctly updated when the state is updated
		"""
		document = mommy.make(MinutesDocument, participants=self.participants, moderator=self.moderator, state=MinutesDocument.UNPUBLISHED)
		university_group = Group.objects.get(name=settings.UNIVERSITY_GROUP_NAME)
		staff_group = Group.objects.get(name=settings.STAFF_GROUP_NAME)

		assign_perm(document.view_permission_name, university_group, document)
		remove_perm(document.view_permission_name, staff_group, document)

		document.state = MinutesDocument.INTERNAL
		document.save()

		document = MinutesDocument.objects.get(url_title=document.url_title)

		checker = ObjectPermissionChecker(university_group)
		self.assertFalse(checker.has_perm(document.view_permission_name, document))
		self.assertFalse(checker.has_perm(document.edit_permission_name, document))
		self.assertFalse(checker.has_perm(document.delete_permission_name, document))

		checker = ObjectPermissionChecker(staff_group)
		self.assertTrue(checker.has_perm(document.view_permission_name, document))
		self.assertTrue(checker.has_perm(document.edit_permission_name, document))
		self.assertTrue(checker.has_perm(document.delete_permission_name, document))
