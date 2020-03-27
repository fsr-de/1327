from unittest import TestCase

from django.conf import settings
from django.contrib.auth.models import Group
from django.urls import reverse
from django_webtest import WebTest
from guardian.core import ObjectPermissionChecker
from guardian.shortcuts import assign_perm
import markdown
from model_bakery import baker
from reversion.models import Version

from _1327.main.utils import slugify
from _1327.minutes.markdown_minutes_extensions import EnterLeavePreprocessor, QuorumPrepocessor, StartEndPreprocessor, \
	VotePreprocessor

from _1327.minutes.models import MinutesDocument
from _1327.user_management.models import UserProfile


class TestEditor(WebTest):
	csrf_checks = False

	@classmethod
	def setUpTestData(cls):
		num_participants = 8

		cls.user = baker.make(UserProfile, is_superuser=True)
		staff_group = Group.objects.get(name=settings.STAFF_GROUP_NAME)
		cls.user.groups.add(staff_group)
		cls.moderator = baker.make(UserProfile)
		cls.participants = baker.make(UserProfile, _quantity=num_participants)
		cls.document = baker.make(MinutesDocument, participants=cls.participants, moderator=cls.moderator)
		assign_perm("minutes.add_minutesdocument", staff_group)

	def test_get_editor(self):
		"""
		Test if the edit page shows the correct content
		"""
		user_without_perms = baker.make(UserProfile)
		response = self.app.get(
			reverse(self.document.get_edit_url_name(), args=[self.document.url_title]),
			expect_errors=True,
			user=user_without_perms
		)
		self.assertEqual(response.status_code, 403)  # test anonymous user cannot access page

		response = self.app.get(reverse(self.document.get_edit_url_name(), args=[self.document.url_title]), user=self.user)
		self.assertEqual(response.status_code, 200)

		form = response.forms['document-form']
		self.assertEqual(form.get('title_en').value, self.document.title_en)
		self.assertEqual(form.get('text_en').value, self.document.text_en)
		self.assertEqual(int(form.get('moderator').value), self.document.moderator.id)
		self.assertEqual(sorted([int(id) for id in form.get('participants').value]), sorted([participant.id for participant in self.document.participants.all()]))
		self.assertTrue("Hidden" in str(form.fields['group'][0]))

	def test_publish_permission_button_displayed(self):
		"""
		Test if the publish and permission buttons are displayed on the correct minutes states
		"""
		unpublished_document = baker.make(MinutesDocument, participants=self.participants, moderator=self.moderator, state=MinutesDocument.UNPUBLISHED)
		unpublished_document.set_all_permissions(Group.objects.get(name="Staff"))
		response = self.app.get(reverse(unpublished_document.get_view_url_name(), args=[unpublished_document.url_title]), user=self.user)
		self.assertIn("Publish", response)
		self.assertNotIn("Permissions", response)

		published_document = baker.make(MinutesDocument, participants=self.participants, moderator=self.moderator, state=MinutesDocument.PUBLISHED)
		published_document.set_all_permissions(Group.objects.get(name="Staff"))
		response = self.app.get(reverse(published_document.get_view_url_name(), args=[published_document.url_title]), user=self.user)
		self.assertNotIn("Publish", response)
		self.assertNotIn("Permissions", response)

		internal_document = baker.make(MinutesDocument, participants=self.participants, moderator=self.moderator, state=MinutesDocument.INTERNAL)
		internal_document.set_all_permissions(Group.objects.get(name="Staff"))
		response = self.app.get(reverse(internal_document.get_view_url_name(), args=[internal_document.url_title]), user=self.user)
		self.assertNotIn("Publish", response)
		self.assertNotIn("Permissions", response)

		custom_document = baker.make(MinutesDocument, participants=self.participants, moderator=self.moderator, state=MinutesDocument.CUSTOM)
		custom_document.set_all_permissions(Group.objects.get(name="Staff"))
		response = self.app.get(reverse(custom_document.get_view_url_name(), args=[custom_document.url_title]), user=self.user)
		self.assertNotIn("Publish", response)
		self.assertIn("Permissions", response)

	def test_publish_button(self):
		"""
		Test if the publish button works
		"""
		staff_group = Group.objects.get(name=settings.STAFF_GROUP_NAME)

		document = baker.make(MinutesDocument, participants=self.participants, moderator=self.moderator, state=MinutesDocument.UNPUBLISHED)
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

		document = baker.make(MinutesDocument, participants=self.participants, moderator=self.moderator, state=MinutesDocument.UNPUBLISHED)
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

		document = baker.make(MinutesDocument, participants=self.participants, moderator=self.moderator, state=MinutesDocument.UNPUBLISHED)
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
		cls.user = baker.make(UserProfile, is_superuser=True)
		cls.minutes_document = baker.make(MinutesDocument)
		cls.group = baker.make(Group)
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

	def test_no_minutes_available_text(self):
		minutes = MinutesDocument.objects.all()
		for document in minutes:
			document.delete()

		# if the user is not logged in he shall see a hint that tells him to log in
		response = self.app.get(reverse("minutes:list", args=[self.group.id]))
		self.assertEqual(response.status_code, 200)
		self.assertIn('No minutes available.', response.body.decode('utf-8'))
		self.assertIn('You might have to', response.body.decode('utf-8'))

		# if the user is logged in there is definetely no minutes document available for him
		response = self.app.get(reverse("minutes:list", args=[self.group.id]), user=self.user)
		self.assertIn('No minutes available.', response.body.decode('utf-8'))
		self.assertNotIn('You might have to', response.body.decode('utf-8'))

		document = baker.make(MinutesDocument)
		document.set_all_permissions(self.group)
		document.save()

		# if the user is logged in and there is a minutes document he should not see any of the hints
		response = self.app.get(reverse("minutes:list", args=[self.group.id]), user=self.user)
		self.assertNotIn('No minutes available.', response.body.decode('utf-8'))
		self.assertNotIn('You might have to', response.body.decode('utf-8'))


class TestSearchMinutes(WebTest):
	csrf_checks = False

	@classmethod
	def setUpTestData(cls):
		cls.user = baker.make(UserProfile, is_superuser=True)

		text1 = "both notO \n Case notB notO \n two notB notO \n two lines notB notO"
		text2 = "in both minutes notO \n one notB \n substring notB notO"
		text3 = "this will never show up notB notO"
		text4 = "<script>alert(Hello);</script> something else"

		text_en = "This is the English Case"

		cls.minutes_document1 = baker.make(MinutesDocument, text_en=text_en, text_de=text1, title_en="MinutesOne", title_de="MinutesOne")
		cls.minutes_document2 = baker.make(MinutesDocument, text_de=text2, title_en="MinutesTwo", title_de="MinutesTwo")
		cls.minutes_document3 = baker.make(MinutesDocument, text_de=text3, title_en="MinutesThree", title_de="MinutesThree")
		cls.minutes_document4 = baker.make(MinutesDocument, text_de=text4, title_en="MinutesFour", title_de="MinutesFour")
		cls.group = baker.make(Group)
		cls.minutes_document1.set_all_permissions(cls.group)
		cls.minutes_document2.set_all_permissions(cls.group)
		cls.minutes_document3.set_all_permissions(cls.group)
		cls.minutes_document4.set_all_permissions(cls.group)

	def test_multiple_languages(self):
		response = self.app.post(reverse('set_lang'), params={'language': 'de'}, user=self.user)
		self.assertEqual(response.status_code, 302)

		search_string = 'Case'
		response = self.app.get(reverse("minutes:list", args=[self.group.id]), user=self.user)

		form = response.forms[0]
		form.set('search_phrase', search_string)

		response = form.submit()

		self.assertIn('MinutesOne', response)
		self.assertNotIn('MinutesTwo', response)
		self.assertNotIn('MinutesThree', response)

		self.assertContains(response, search_string, count=2)

		self.assertIn("<li><i>This is the English <b>Case</b></i></li>", response)
		self.assertIn("<li> <b>Case</b> notB notO </li>", response)

	def test_two_minutes_results(self):
		search_string = "both"

		response = self.app.get(reverse("minutes:list", args=[self.group.id]), user=self.user)

		form = response.forms[0]
		form.set('search_phrase', search_string)

		response = form.submit()

		self.assertIn('MinutesOne', response)
		self.assertIn('MinutesTwo', response)
		self.assertNotIn('MinutesThree', response)

		self.assertIn('<b>both</b> notO', response)
		self.assertIn('in <b>both</b> minutes notO', response)
		self.assertNotIn('notB', response.body.decode('utf-8'))

	def test_one_minute_results(self):
		search_string = "one"

		response = self.app.get(reverse("minutes:list", args=[self.group.id]), user=self.user)

		form = response.forms[0]
		form.set('search_phrase', search_string)

		response = form.submit()

		self.assertIn('MinutesTwo', response)
		self.assertNotIn('MinutesOne', response)
		self.assertNotIn('MinutesThree', response)

		self.assertIn('<b>one</b> notB', response)
		self.assertNotIn('notO', response)

	def test_two_line_results(self):
		search_string = "two"

		response = self.app.get(reverse("minutes:list", args=[self.group.id]), user=self.user)

		form = response.forms[0]
		form.set('search_phrase', search_string)

		response = form.submit()

		self.assertIn('MinutesOne', response)
		self.assertNotIn('MinutesTwo', response)
		self.assertNotIn('MinutesThree', response)

		self.assertIn('<b>two</b> notB notO', response)
		self.assertIn('<b>two</b> lines notB notO', response)

	def test_case_insensitive_result(self):
		search_string = "case"

		response = self.app.get(reverse("minutes:list", args=[self.group.id]), user=self.user)

		form = response.forms[0]
		form.set('search_phrase', search_string)

		response = form.submit()

		self.assertIn('MinutesOne', response)
		self.assertNotIn('MinutesTwo', response)
		self.assertNotIn('MinutesThree', response)

		self.assertIn('<b>Case</b> notB notO', response)

	def test_substring_result(self):
		search_string = "bstrin"

		response = self.app.get(reverse("minutes:list", args=[self.group.id]), user=self.user)

		form = response.forms[0]
		form.set('search_phrase', search_string)

		response = form.submit()

		self.assertIn('MinutesTwo', response)
		self.assertNotIn('MinutesOne', response)
		self.assertNotIn('MinutesThree', response)

		self.assertIn('su<b>bstrin</b>g notB notO', response)

	def test_nothing_found_message(self):
		search_string = "not in the minutes"

		response = self.app.get(reverse("minutes:list", args=[self.group.id]), user=self.user)

		form = response.forms[0]
		form.set('search_phrase', search_string)

		response = form.submit()

		self.assertIn('No documents containing "not in the minutes" found.', response.body.decode('utf-8'))
		self.assertNotIn('notB', response)
		self.assertNotIn('notO', response)

	def test_correct_escaping(self):
		search_string = "<script>alert(Hello);</script>"

		response = self.app.get(reverse("minutes:list", args=[self.group.id]), user=self.user)

		form = response.forms[0]
		form.set('search_phrase', search_string)

		response = form.submit()

		self.assertIn('<b>&lt;script&gt;alert(Hello);&lt;/script&gt;</b> something else', response.body.decode('utf-8'))


class TestNewMinutesDocument(WebTest):
	csrf_checks = False

	@classmethod
	def setUpTestData(cls):
		cls.user = baker.make(UserProfile)
		cls.group = baker.make(Group)
		cls.user.groups.add(cls.group)
		assign_perm("minutes.add_minutesdocument", cls.group)

		# add another user to group
		cls.group.user_set.add(baker.make(UserProfile))

	def test_save_first_minutes_document(self):
		# get the editor page and save the site
		response = self.app.get(reverse('documents:create', args=['minutesdocument']) + '?group={}'.format(self.group.id), user=self.user)
		self.assertEqual(response.status_code, 200)

		form = response.forms['document-form']
		text = "Lorem ipsum"
		form.set('text_en', text)
		form.set('comment', text)
		form.set('url_title', slugify(text))

		response = form.submit().follow()
		self.assertEqual(response.status_code, 200)

		document = MinutesDocument.objects.get(url_title=slugify(text))

		# check whether number of versions is correct
		versions = Version.objects.get_for_object(document)
		self.assertEqual(len(versions), 1)

		# check whether the properties of the new document are correct
		self.assertEqual((document.title_en, document.title_de), MinutesDocument.generate_new_title())
		self.assertEqual(document.author, self.user)
		self.assertEqual(document.moderator, self.user)
		self.assertEqual(document.text_en, text)
		self.assertEqual(versions[0].revision.get_comment(), text)
		self.assertListEqual(list(document.participants.all().order_by('username')), list(self.group.user_set.all().order_by('username')))

		checker = ObjectPermissionChecker(self.group)
		self.assertTrue(checker.has_perm(document.edit_permission_name, document))

	def test_save_another_minutes_document(self):
		test_title = "Test title"
		test_moderator = baker.make(UserProfile)
		first_document = baker.make(MinutesDocument, title_en=test_title, moderator=test_moderator)
		first_document.set_all_permissions(self.group)

		# get the editor page and save the site
		response = self.app.get(reverse('documents:create', args=['minutesdocument']) + '?group={}'.format(self.group.id), user=self.user)
		self.assertEqual(response.status_code, 200)

		form = response.forms['document-form']
		text = "Lorem ipsum"
		form.set('text_en', text)
		form.set('comment', text)
		form.set('url_title', slugify(text))

		response = form.submit().follow()
		self.assertEqual(response.status_code, 200)

		document = MinutesDocument.objects.get(url_title=slugify(text))

		# check whether the properties of the new document are correct
		self.assertEqual(document.title_en, test_title)  # should be taken from previous minutes document
		self.assertEqual(document.moderator, test_moderator)  # should be taken from previous minutes document
		self.assertEqual(document.author, self.user)
		self.assertEqual(document.text_en, text)
		self.assertListEqual(list(document.participants.all().order_by('username')), list(self.group.user_set.all().order_by('username')))

	def test_group_field_hidden_when_user_has_one_group(self):
		response = self.app.get(reverse('documents:create', args=['minutesdocument']) + '?group={}'.format(self.group.id), user=self.user)
		self.assertEqual(response.status_code, 200)

		form = response.forms['document-form']
		self.assertTrue("Hidden" in str(form.fields['group'][0]))

	def test_group_field_not_hidden_when_user_has_multiple_groups(self):
		other_group = baker.make(Group)
		self.user.groups.add(other_group)
		assign_perm("minutes.add_minutesdocument", other_group)
		response = self.app.get(reverse('documents:create', args=['minutesdocument']) + '?group={}'.format(self.group.id), user=self.user)
		self.assertEqual(response.status_code, 200)

		form = response.forms['document-form']
		self.assertFalse("Hidden" in str(form.fields['group'][0]))


class TestMarkdownMinutesExtension(TestCase):
	def setUp(self):
		self.md = markdown.Markdown(
			extensions=[
				'_1327.minutes.markdown_minutes_extensions',
			]
		)
		self.vote_preprocessor = VotePreprocessor(self.md)
		self.start_end_preprocessor = StartEndPreprocessor(self.md)
		self.quorum_preprocessor = QuorumPrepocessor(self.md)
		self.enter_leave_preprocessor = EnterLeavePreprocessor(self.md)
		self.base_text = "This is a nice template text, where we will add stuff that shall be preprocessed: {}"

	def test_vote_preprocessor(self):
		vote_text = "[1|1|3]"
		processed_text = self.vote_preprocessor.run([self.base_text.format(vote_text)])[0]
		self.assertIn("**{}**".format(vote_text), processed_text)

	def test_start_end_preprocessor(self):
		start_text = "|start|(15:00)"
		processed_text = self.start_end_preprocessor.run([self.base_text.format(start_text)])[0]
		self.assertIn("*Begin of meeting: 15:00*", processed_text)

		end_text = "|end|(16:00)"
		processed_text = self.start_end_preprocessor.run([self.base_text.format(end_text)])[0]
		self.assertIn("*End of meeting: 16:00*", processed_text)

	def test_quorum_preprocessor(self):
		enough_quorum_text = "|quorum|(6/7)"
		processed_text = self.quorum_preprocessor.run([self.base_text.format(enough_quorum_text)])[0]
		self.assertIn("*6/7 present → quorate*", processed_text)

		not_enough_quorum_text = "|quorum|(3/7)"
		processed_text = self.quorum_preprocessor.run([self.base_text.format(not_enough_quorum_text)])[0]
		self.assertIn("*3/7 present → not quorate*", processed_text)

	def test_enter_leave_preprocessor(self):
		enter_text_without_mean = "|enter|(14:30)(User)"
		processed_text = self.enter_leave_preprocessor.run([self.base_text.format(enter_text_without_mean)])[0]
		self.assertIn("*14:30: User enters the meeting*", processed_text)
		self.assertNotIn("via", processed_text)

		enter_text_with_mean = enter_text_without_mean + "(Hangout)"
		processed_text = self.enter_leave_preprocessor.run([self.base_text.format(enter_text_with_mean)])[0]
		self.assertIn("*14:30: User enters the meeting via Hangout*", processed_text)

		leave_text = "|leave|(15:30)(User)"
		processed_text = self.enter_leave_preprocessor.run([self.base_text.format(leave_text)])[0]
		self.assertIn("*15:30: User leaves the meeting*", processed_text)

		leave_text_with_space = "|leave|(15:30)(User with Spaces)"
		processed_text = self.enter_leave_preprocessor.run([self.base_text.format(leave_text_with_space)])[0]
		self.assertIn("*15:30: User with Spaces leaves the meeting*", processed_text)
