from django.conf import settings
from django.contrib.auth.models import Group
from django.urls import reverse
from django_webtest import WebTest
from guardian.core import ObjectPermissionChecker
from guardian.shortcuts import assign_perm
from model_mommy import mommy
from reversion.models import Version

from _1327.main.utils import slugify
from _1327.minutes.models import MinutesDocument
from _1327.user_management.models import UserProfile


class TestEditor(WebTest):
	csrf_checks = False

	@classmethod
	def setUpTestData(cls):
		num_participants = 8

		cls.user = mommy.make(UserProfile, is_superuser=True)
		cls.user.groups.add(Group.objects.get(name=settings.STAFF_GROUP_NAME))
		cls.moderator = mommy.make(UserProfile)
		cls.participants = mommy.make(UserProfile, _quantity=num_participants)
		cls.document = mommy.make(MinutesDocument, participants=cls.participants, moderator=cls.moderator)
		cls.document.set_all_permissions(mommy.make(Group))

	def test_get_editor(self):
		"""
		Test if the edit page shows the correct content
		"""
		user_without_perms = mommy.make(UserProfile)
		response = self.app.get(
			reverse(self.document.get_edit_url_name(), args=[self.document.url_title]),
			expect_errors=True,
			user=user_without_perms
		)
		self.assertEqual(response.status_code, 403)  # test anonymous user cannot access page

		response = self.app.get(reverse(self.document.get_edit_url_name(), args=[self.document.url_title]), user=self.user)
		self.assertEqual(response.status_code, 200)

		form = response.forms[0]
		self.assertEqual(form.get('title').value, self.document.title)
		self.assertEqual(form.get('text').value, self.document.text)
		self.assertEqual(int(form.get('moderator').value), self.document.moderator.id)
		self.assertEqual(sorted([int(id) for id in form.get('participants').value]), sorted([participant.id for participant in self.document.participants.all()]))
		self.assertTrue("Hidden" in str(form.fields['group'][0]))

	def test_publish_permission_button_displayed(self):
		"""
		Test if the publish and permission buttons are displayed on the correct minutes states
		"""
		unpublished_document = mommy.make(MinutesDocument, participants=self.participants, moderator=self.moderator, state=MinutesDocument.UNPUBLISHED)
		unpublished_document.set_all_permissions(Group.objects.get(name="Staff"))
		response = self.app.get(reverse(unpublished_document.get_view_url_name(), args=[unpublished_document.url_title]), user=self.user)
		self.assertIn("Publish", response)
		self.assertNotIn("Permissions", response)

		published_document = mommy.make(MinutesDocument, participants=self.participants, moderator=self.moderator, state=MinutesDocument.PUBLISHED)
		published_document.set_all_permissions(Group.objects.get(name="Staff"))
		response = self.app.get(reverse(published_document.get_view_url_name(), args=[published_document.url_title]), user=self.user)
		self.assertNotIn("Publish", response)
		self.assertNotIn("Permissions", response)

		internal_document = mommy.make(MinutesDocument, participants=self.participants, moderator=self.moderator, state=MinutesDocument.INTERNAL)
		internal_document.set_all_permissions(Group.objects.get(name="Staff"))
		response = self.app.get(reverse(internal_document.get_view_url_name(), args=[internal_document.url_title]), user=self.user)
		self.assertNotIn("Publish", response)
		self.assertNotIn("Permissions", response)

		custom_document = mommy.make(MinutesDocument, participants=self.participants, moderator=self.moderator, state=MinutesDocument.CUSTOM)
		custom_document.set_all_permissions(Group.objects.get(name="Staff"))
		response = self.app.get(reverse(custom_document.get_view_url_name(), args=[custom_document.url_title]), user=self.user)
		self.assertNotIn("Publish", response)
		self.assertIn("Permissions", response)

	def test_publish_button(self):
		"""
		Test if the publish button works
		"""
		staff_group = Group.objects.get(name=settings.STAFF_GROUP_NAME)

		document = mommy.make(MinutesDocument, participants=self.participants, moderator=self.moderator, state=MinutesDocument.UNPUBLISHED)
		document.set_all_permissions(staff_group)

		# The 1 sets the state to published
		self.app.get(reverse('documents:publish', args=[document.url_title, 1]), user=self.user)

		document = MinutesDocument.objects.get(url_title=document.url_title)
		self.assertEqual(document.state, MinutesDocument.PUBLISHED)

		group = Group.objects.get(name=settings.UNIVERSITY_GROUP_NAME)
		checker = ObjectPermissionChecker(group)
		self.assertTrue(checker.has_perm(document.view_permission_name, document))
		self.assertFalse(checker.has_perm(document.edit_permission_name, document))
		self.assertFalse(checker.has_perm(document.delete_permission_name, document))

		group = Group.objects.get(name=settings.STUDENT_GROUP_NAME)
		checker = ObjectPermissionChecker(group)
		self.assertTrue(checker.has_perm(document.view_permission_name, document))
		self.assertFalse(checker.has_perm(document.edit_permission_name, document))
		self.assertFalse(checker.has_perm(document.delete_permission_name, document))

		checker = ObjectPermissionChecker(staff_group)
		self.assertTrue(checker.has_perm(document.view_permission_name, document))
		self.assertTrue(checker.has_perm(document.edit_permission_name, document))
		self.assertTrue(checker.has_perm(document.delete_permission_name, document))

	def test_publish_student_button(self):
		"""
		Test if the publish for students only button works
		"""
		staff_group = Group.objects.get(name=settings.STAFF_GROUP_NAME)

		document = mommy.make(MinutesDocument, participants=self.participants, moderator=self.moderator, state=MinutesDocument.UNPUBLISHED)
		document.set_all_permissions(staff_group)

		# The 4 sets the state to published_student
		self.app.get(reverse('documents:publish', args=[document.url_title, 4]), user=self.user)

		document = MinutesDocument.objects.get(url_title=document.url_title)
		self.assertEqual(document.state, MinutesDocument.PUBLISHED_STUDENT)

		group = Group.objects.get(name=settings.UNIVERSITY_GROUP_NAME)
		checker = ObjectPermissionChecker(group)
		self.assertFalse(checker.has_perm(document.view_permission_name, document))
		self.assertFalse(checker.has_perm(document.edit_permission_name, document))
		self.assertFalse(checker.has_perm(document.delete_permission_name, document))

		group = Group.objects.get(name=settings.STUDENT_GROUP_NAME)
		checker = ObjectPermissionChecker(group)
		self.assertTrue(checker.has_perm(document.view_permission_name, document))
		self.assertFalse(checker.has_perm(document.edit_permission_name, document))
		self.assertFalse(checker.has_perm(document.delete_permission_name, document))

		checker = ObjectPermissionChecker(staff_group)
		self.assertTrue(checker.has_perm(document.view_permission_name, document))
		self.assertTrue(checker.has_perm(document.edit_permission_name, document))
		self.assertTrue(checker.has_perm(document.delete_permission_name, document))

	def test_state_permission_update(self):
		"""
		Test if the permission are correctly updated when the state is updated
		"""
		staff_group = Group.objects.get(name=settings.STAFF_GROUP_NAME)
		university_group = Group.objects.get(name=settings.UNIVERSITY_GROUP_NAME)

		document = mommy.make(MinutesDocument, participants=self.participants, moderator=self.moderator, state=MinutesDocument.UNPUBLISHED)
		document.set_all_permissions(staff_group)

		assign_perm(document.view_permission_name, university_group, document)

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


class TestMinutesList(WebTest):
	csrf_checks = False

	@classmethod
	def setUpTestData(cls):
		cls.user = mommy.make(UserProfile, is_superuser=True)
		cls.minutes_document = mommy.make(MinutesDocument)
		cls.group = mommy.make(Group)
		cls.minutes_document.set_all_permissions(cls.group)

	def test_list_permission_display(self):
		"""
		Test if the permissions are correctly shown in the minutes list
		"""
		self.assertEqual(MinutesDocument.objects.count(), 1)

		self.minutes_document.state = MinutesDocument.UNPUBLISHED
		self.minutes_document.save()
		response = self.app.get(reverse("minutes:list", args=[self.group.id]), user=self.user)
		self.assertIn("glyphicon-alert", response)

		self.minutes_document.state = MinutesDocument.PUBLISHED
		self.minutes_document.save()
		response = self.app.get(reverse("minutes:list", args=[self.group.id]), user=self.user)
		self.assertIn("glyphicon-education", response)

		self.minutes_document.state = MinutesDocument.INTERNAL
		self.minutes_document.save()
		response = self.app.get(reverse("minutes:list", args=[self.group.id]), user=self.user)
		self.assertIn("glyphicon-lock", response)

		self.minutes_document.state = MinutesDocument.CUSTOM
		self.minutes_document.save()
		response = self.app.get(reverse("minutes:list", args=[self.group.id]), user=self.user)
		self.assertIn("glyphicon-cog", response)

		self.minutes_document.state = MinutesDocument.PUBLISHED_STUDENT
		self.minutes_document.save()
		response = self.app.get(reverse("minutes:list", args=[self.group.id]), user=self.user)
		self.assertIn("glyphicon-user", response)


class TestNewMinutesDocument(WebTest):
	csrf_checks = False

	@classmethod
	def setUpTestData(cls):
		cls.user = mommy.make(UserProfile, is_superuser=True)

	def test_save_new_minutes_document(self):
		# get the editor page and save the site
		group = mommy.make(Group)
		group.user_set.add(self.user)
		response = self.app.get(reverse('documents:create', args=['minutesdocument']), user=self.user)
		self.assertEqual(response.status_code, 200)

		form = response.forms[0]
		text = "Lorem ipsum"
		form.set('text', text)
		form.set('title', text)
		form.set('participants', [self.user.pk])
		form.set('comment', text)
		form.set('url_title', slugify(text))
		form.set('group', group.pk)

		response = form.submit().follow()
		self.assertEqual(response.status_code, 200)

		document = MinutesDocument.objects.get(title=text)

		# check whether number of versions is correct
		versions = Version.objects.get_for_object(document)
		self.assertEqual(len(versions), 1)

		# check whether the properties of the new document are correct
		self.assertEqual(document.title, text)
		self.assertEqual(document.text, text)
		self.assertEqual(versions[0].revision.comment, text)

	def test_group_field_hidden_when_user_has_one_group(self):
		group = mommy.make(Group)
		self.user.groups.add(group)
		response = self.app.get(reverse('documents:create', args=['minutesdocument']), user=self.user)
		self.assertEqual(response.status_code, 200)

		form = response.forms[0]
		self.assertTrue("Hidden" in str(form.fields['group'][0]))

	def test_group_field_not_hidden_when_user_has_multiple_groups(self):
		groups = mommy.make(Group, _quantity=2)
		self.user.groups.add(*groups)
		response = self.app.get(reverse('documents:create', args=['minutesdocument']), user=self.user)
		self.assertEqual(response.status_code, 200)

		form = response.forms[0]
		self.assertFalse("Hidden" in str(form.fields['group'][0]))
