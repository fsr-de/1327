from datetime import datetime
import json
import re
import tempfile

from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile
from django.db import transaction
from django.test import TestCase
from django.urls import reverse
from django_webtest import WebTest
from guardian.shortcuts import assign_perm, get_perms, get_perms_for_model, remove_perm
from guardian.utils import get_anonymous_user
import markdown
from model_bakery import baker
from reversion import revisions
from reversion.models import Version

from _1327.documents.markdown_internal_link_extension import InternalLinksMarkdownExtension
from _1327.documents.markdown_scaled_image_extension import SCALED_IMAGE_LINK_RE, ScaledImagePattern
from _1327.information_pages.models import InformationDocument
from _1327.main.utils import EscapeHtml, slugify
from _1327.minutes.models import MinutesDocument
from _1327.polls.models import Poll
from _1327.user_management.models import UserProfile

from .models import Attachment, Document, TemporaryDocumentText


class TestInternalLinkMarkDown(TestCase):
	@classmethod
	def setUpTestData(cls):
		cls.user = baker.make(UserProfile, is_superuser=True)

		cls.md = markdown.Markdown(extensions=[EscapeHtml(), InternalLinksMarkdownExtension(), 'markdown.extensions.tables'])

		cls.document = baker.prepare(InformationDocument, text_en="text")
		with transaction.atomic(), revisions.create_revision():
				cls.document.save()
				revisions.set_user(cls.user)
				revisions.set_comment('test version')

	def test_information_documents(self):
		text = self.md.convert('Some text before [a link](document:' + str(self.document.id) + ') and some more text.')
		link = reverse(self.document.get_view_url_name(), args=[self.document.url_title])
		self.assertIn('Some text before <a href="' + link + '">a link</a> and some more text.', text)

	def test_multiple_information_documents(self):
		text = self.md.convert('Some text before [a link](document:' + str(self.document.id) + '), [another link](document:' + str(self.document.id) + ') and some more text.')
		link = reverse(self.document.get_view_url_name(), args=[self.document.url_title])
		self.assertIn('Some text before <a href="' + link + '">a link</a>, <a href="' + link + '">another link</a> and some more text.', text)

	def test_document_deleted(self):
		document = InformationDocument.objects.get()
		document.delete()
		text = self.md.convert('[description](document:{})'.format(document.id))
		self.assertIn('<a>[missing link]</a>', text)


class TestRevertion(WebTest):
	csrf_checks = False

	@classmethod
	def setUpTestData(cls):
		cls.user = baker.make(UserProfile, is_superuser=True)

		cls.document = baker.prepare(Document, text_en="text")
		with transaction.atomic(), revisions.create_revision():
				cls.document.save()
				revisions.set_user(cls.user)
				revisions.set_comment('test version')

		# create a second version
		cls.document.text_en += '\nmore text'
		with transaction.atomic(), revisions.create_revision():
				cls.document.save()
				revisions.set_user(cls.user)
				revisions.set_comment('added more text')

	def test_only_admin_may_revert(self):
		versions = Version.objects.get_for_object(self.document)
		self.assertEqual(len(versions), 2)

		user_without_perms = baker.make(UserProfile)
		response = self.app.post(
			reverse('documents:revert'),
			params={'id': versions[1].pk, 'url_title': self.document.url_title},
			status=404,
			user=user_without_perms,
		)
		self.assertEqual(response.status_code, 404)

		response = self.app.post(
			reverse('documents:revert'),
			params={'id': versions[1].pk, 'url_title': self.document.url_title},
			status=403,
			xhr=True,
			user=user_without_perms,
		)
		self.assertEqual(response.status_code, 403)

		response = self.app.post(
			reverse('documents:revert'),
			params={'id': versions[1].pk, 'url_title': self.document.url_title},
			user=self.user,
			status=404
		)
		self.assertEqual(response.status_code, 404)

		response = self.app.post(
			reverse('documents:revert'),
			params={'id': versions[1].pk, 'url_title': self.document.url_title},
			user=self.user,
			xhr=True
		)
		self.assertEqual(response.status_code, 200)

	def test_revert_document(self):
		versions = Version.objects.get_for_object(self.document)
		self.assertEqual(len(versions), 2)

		# second step try to revert to old version
		response = self.app.post(
			reverse('documents:revert'),
			params={'id': versions[1].pk, 'url_title': self.document.url_title},
			user=self.user,
			xhr=True
		)
		self.assertEqual(response.status_code, 200)

		versions = Version.objects.get_for_object(self.document)
		self.assertEqual(len(versions), 3)
		self.assertEqual(versions[0].object.text_en, "text")
		self.assertEqual(versions[0].revision.get_comment(), 'reverted to revision "test version" (at {date})'.format(
			date=datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
		))

	def test_revert_to_different_url(self):
		document = Document.objects.get()
		old_url = document.url_title

		document.url_title = 'new/url'
		with transaction.atomic(), revisions.create_revision():
			document.save()
			revisions.set_user(self.user)
			revisions.set_comment('changed url')

		versions = Version.objects.get_for_object(document)
		response = self.app.post(
			reverse('documents:revert'),
			params={'id': versions[2].pk, 'url_title': document.url_title},
			user=self.user,
			xhr=True
		)

		self.assertEqual(response.status_code, 200)
		self.assertIn(reverse('versions', args=[old_url]), response.body.decode('utf-8'))

	def test_version_creation(self):
		Document.objects.all().delete()
		self.assertEqual(Document.objects.count(), 0)

		def submit_form(text, form, group, sub_class):
			for field_name in form.fields.keys():
				if field_name is not None and 'text' in field_name:
					form.set(field_name, text)
			form.set('comment', text)
			form.set('group', group.pk)
			if sub_class == MinutesDocument:
				participants_field = form.get('participants')
				participants_field.select_multiple([participants_field.options[0][0]])
			response = form.submit().follow()
			self.assertEqual(response.status_code, 200)

		group = baker.make(Group)
		assign_perm("minutes.add_minutesdocument", group)
		assign_perm("information_pages.add_informationdocument", group)
		assign_perm("polls.add_poll", group)

		for expected_count, sub_class in enumerate(Document.__subclasses__(), start=1):
			response = self.app.get(reverse('documents:create', args=[sub_class.__name__.lower()]), user=self.user)
			self.assertEqual(response.status_code, 200)
			form = response.forms['document-form']

			url_title = form.get('url_title').value
			text_1 = 'something'
			submit_form(text_1, form, group, sub_class)

			self.assertEqual(Document.objects.count(), expected_count)
			document = Document.objects.get(url_title=url_title)
			response = self.app.get(reverse('edit', args=[document.url_title]), user=self.user)

			form = response.forms['document-form']

			text_2 = 'something else'
			submit_form(text_2, form, group, sub_class)

			versions = Version.objects.get_for_object(document).reverse()
			self.assertEqual(len(versions), 2)
			for version, text in zip(versions, [text_1, text_2]):
				self.assertEqual(version.field_dict['text_en'], text)


class TestAutosave(WebTest):
	csrf_checks = False
	extra_environ = {'HTTP_ACCEPT_LANGUAGE': 'en'}

	@classmethod
	def setUpTestData(cls):
		cls.user = baker.make(UserProfile, is_superuser=True)
		cls.user.groups.add(Group.objects.get(name=settings.STAFF_GROUP_NAME))
		cls.group = baker.make(Group)

		cls.document = baker.prepare(InformationDocument, text_de="text_de", title_de="title_de", text_en="text_en")
		with transaction.atomic(), revisions.create_revision():
				cls.document.save()
				revisions.set_user(cls.user)
				revisions.set_comment('test version')

	def test_autosave(self):
		# document text should be text
		response = self.app.get(reverse(self.document.get_edit_url_name(), args=[self.document.url_title]), user=self.user)
		self.assertEqual(response.status_code, 200)
		form = response.forms['document-form']
		self.assertEqual(form.get('text_de').value, 'text_de')
		self.assertEqual(form.get('text_en').value, 'text_en')

		# autosave AUTO
		response = self.app.post(
			reverse('documents:autosave', args=[self.document.url_title]),
			params={'text_de': 'AUTO_de', 'text_en': 'AUTO_en', 'title_en': form.get('title_en').value, 'comment': ''},
			user=self.user,
			xhr=True
		)
		self.assertEqual(response.status_code, 200)

		# if not loading autosave text should be still text
		response = self.app.get(reverse(self.document.get_edit_url_name(), args=[self.document.url_title]), user=self.user)
		self.assertEqual(response.status_code, 200)
		form = response.forms['document-form']
		self.assertEqual(form.get('text_de').value, 'text_de')
		self.assertEqual(form.get('text_en').value, 'text_en')

		# if loading autosave text should be AUTO
		autosave = TemporaryDocumentText.objects.get()
		response = self.app.get(
			reverse(self.document.get_edit_url_name(), args=[self.document.url_title]),
			params={'restore': autosave.id},
			user=self.user
		)
		self.assertEqual(response.status_code, 200)
		form = response.forms['document-form']
		self.assertEqual(form.get('text_de').value, 'AUTO_de')
		self.assertEqual(form.get('text_en').value, 'AUTO_en')

		# second autosave AUTO2
		response = self.app.post(
			reverse('documents:autosave', args=[self.document.url_title]),
			params={'text_de': 'AUTO2_de', 'text_en': 'AUTO2_en', 'title_en': form.get('title_en').value, 'comment': ''},
			user=self.user,
			xhr=True
		)
		self.assertEqual(response.status_code, 200)

		# if loading autosave text should be AUTO2
		autosave = TemporaryDocumentText.objects.get()
		response = self.app.get(
			reverse(self.document.get_edit_url_name(), args=[self.document.url_title]),
			params={'restore': autosave.id},
			user=self.user
		)
		self.assertEqual(response.status_code, 200)
		form = response.forms['document-form']
		self.assertEqual(form.get('text_de').value, 'AUTO2_de')
		self.assertEqual(form.get('text_en').value, 'AUTO2_en')

	def test_autosave_not_logged_in(self):
		response = self.app.get(reverse('documents:create', args=['informationdocument']), user=self.user)
		self.assertEqual(response.status_code, 200)

		form = response.forms['document-form']
		url_title = slugify(form.get('title_en').value)

		# autosave AUTO
		response = self.app.post(
			reverse('documents:autosave', args=[url_title]),
			params={'text_en': 'AUTO', 'title_en': form.get('title_en').value, 'comment': ''},
			xhr=True,
			user=get_anonymous_user(),
			expect_errors=True,
		)
		self.assertEqual(response.status_code, 403)

	def test_autosave_newPage(self):
		# create document
		response = self.app.get(reverse('documents:create', args=['informationdocument']), user=self.user)
		self.assertEqual(response.status_code, 200)
		form = response.forms['document-form']
		# we need to scrape the url_title from the action as we can not get it from the url_title field in the form
		url_title = re.search(r'^/(?P<url_title>temp_.+)/', form.action).group('url_title')

		# autosave AUTO
		response = self.app.post(
			reverse('documents:autosave', args=[url_title]),
			params={'text_en': 'AUTO', 'title_en': form.get('title_en').value, 'comment': ''},
			xhr=True
		)
		self.assertEqual(response.status_code, 200)

		self.assertEqual(TemporaryDocumentText.objects.count(), 1)
		autosave = TemporaryDocumentText.objects.first()

		# on the new page site should be a banner with a restore link
		response = self.app.get(reverse('documents:create', args=['informationdocument']), user=self.user)
		self.assertEqual(response.status_code, 200)
		self.assertIn((reverse('edit', args=[url_title]) + '?restore={}'.format(autosave.id)), str(response.body))

		user2 = baker.make(UserProfile, is_superuser=True)
		user2.groups.add(Group.objects.get(name=settings.STAFF_GROUP_NAME))
		# on the new page site should be a banner with a restore link but not for another user
		response = self.app.get(reverse('documents:create', args=['informationdocument']), user=user2)
		self.assertEqual(response.status_code, 200)
		self.assertNotIn((reverse('edit', args=[url_title]) + '?restore={}'.format(autosave.id)), str(response.body))

		# create second document
		response = self.app.get(reverse('documents:create', args=['informationdocument']), user=self.user)
		self.assertEqual(response.status_code, 200)
		form = response.forms['document-form']
		# we need to scrape the url_title from the action as we can not get it from the url_title field in the form
		url_title2 = re.search(r'^/(?P<url_title>temp_.+)/', form.action).group('url_title')

		# autosave second document AUTO
		response = self.app.post(
			reverse('documents:autosave', args=[url_title2]),
			params={'text_en': 'AUTO', 'title_en': form.get('title_en').value, 'comment': ''},
			user=self.user,
			xhr=True
		)
		self.assertEqual(response.status_code, 200)

		# on the new page site should be a banner with a restore link for both sites
		response = self.app.get(reverse('documents:create', args=['informationdocument']), user=self.user)
		for urltitle, autosave in zip([url_title, url_title2], TemporaryDocumentText.objects.all()):
			self.assertIn((reverse('edit', args=[urltitle]) + '?restore={}'.format(autosave.id)), str(response.body))

		# if not loading autosave text should be still empty
		response = self.app.get(reverse('edit', args=[url_title]), user=self.user)
		self.assertEqual(response.status_code, 200)
		form = response.forms['document-form']
		self.assertEqual(form.get('text_en').value, '')

		# if loading autosave text should be AUTO
		autosave = TemporaryDocumentText.objects.first()
		response = self.app.get(
			reverse('edit', args=[url_title]),
			params={'restore': autosave.id},
			user=self.user
		)
		self.assertEqual(response.status_code, 200)
		form = response.forms['document-form']
		self.assertEqual(form.get('text_en').value, 'AUTO')

	def test_create_autosave_non_superuser(self):
		# test every document type
		for klass in Document.__subclasses__():
			user = baker.make(UserProfile)
			group = baker.make(Group)
			group.user_set.add(user)
			# add the 'add' permission to the group for that document type
			content_type = ContentType.objects.get_for_model(klass)
			permission_name = "{}.add_{}".format(content_type.app_label, content_type.model.lower())
			assign_perm(permission_name, group)
			self.assertTrue(user.has_perm(permission_name))

			# try to perform an autosave
			response = self.app.get(reverse('documents:create', args=[content_type.model.lower()]), user=user)
			self.assertEqual(response.status_code, 200)
			form = response.forms['document-form']
			# we need to scrape the url_title from the action as we can not get it from the url_title field in the form
			url_title = re.search(r'/(?P<url_title>temp_.+)/', form.action).group('url_title')

			response = self.app.post(
				reverse('documents:autosave', args=[url_title]),
				params={'text_en': 'AUTO', 'title_en': form.get('title_en').value, 'comment': ''},
				xhr=True,
				user=user,
			)
			self.assertEqual(response.status_code, 200)

	def test_autosave_with_different_document_types(self):
		# create document
		assign_perm("information_pages.add_informationdocument", self.group)
		response = self.app.get(reverse('documents:create', args=['informationdocument']), user=self.user)
		self.assertEqual(response.status_code, 200)
		form = response.forms['document-form']
		# we need to scrape the url_title from the action as we can not get it from the url_title field in the form
		url_title = re.search(r'^/(?P<url_title>temp_.+)/', form.action).group('url_title')

		# autosave AUTO
		response = self.app.post(
			reverse('documents:autosave', args=[url_title]),
			params={'text_en': 'AUTO', 'title_en': form.get('title_en').value, 'comment': '', 'group': baker.make(Group)},
			xhr=True
		)
		self.assertEqual(response.status_code, 200)

		self.assertEqual(TemporaryDocumentText.objects.count(), 1)
		autosave = TemporaryDocumentText.objects.first()

		# there should be no restore link on creation page for different document type
		assign_perm("polls.add_poll", self.group)
		response = self.app.get(reverse('documents:create', args=['poll']), user=self.user)
		self.assertNotIn((reverse('edit', args=[url_title]) + '?restore={}'.format(autosave.id)), str(response.body))

		# on the new page site should be a banner with a restore link
		response = self.app.get(reverse('documents:create', args=['informationdocument']), user=self.user)
		self.assertEqual(response.status_code, 200)
		self.assertIn((reverse('edit', args=[url_title]) + '?restore={}'.format(autosave.id)), str(response.body))

	def test_autosave_not_possible_to_view_without_permissions(self):
		autosave = baker.make(TemporaryDocumentText, document=self.document, author=self.user)

		self.assertFalse(self.document.has_perms())

		user_without_permissions = baker.make(UserProfile)
		response = self.app.get(
			reverse(autosave.document.get_edit_url_name(), args=[autosave.document.url_title]),
			expect_errors=True,
			user=user_without_permissions
		)
		self.assertEqual(response.status_code, 403)

	def test_autosave_possible_to_view_autosave_with_permissions(self):
		autosave = baker.make(TemporaryDocumentText, document=self.document, author=self.user)

		self.assertFalse(self.document.has_perms())
		assign_perm(self.document.add_permission_name, self.user)

		response = self.app.get(reverse(autosave.document.get_edit_url_name(), args=[autosave.document.url_title]), user=self.user)
		self.assertEqual(response.status_code, 200)
		self.assertIn("The text of this document was autosaved on", response.body.decode('utf-8'))

	def test_autosave_not_possible_to_view_because_not_author(self):
		autosave = baker.make(TemporaryDocumentText, document=self.document)

		self.assertFalse(self.document.has_perms())

		response = self.app.get(reverse(autosave.document.get_edit_url_name(), args=[autosave.document.url_title]), expect_errors=True, user=self.user)
		self.assertNotIn('?restore={}'.format(autosave.id), response.body.decode('utf-8'))

	def test_can_not_restore_autosave_of_different_user(self):
		baker.make(TemporaryDocumentText, document=self.document, author=self.user)
		second_user = baker.make(UserProfile)
		second_document = baker.prepare(InformationDocument, text_en="text_en")

		with transaction.atomic(), revisions.create_revision():
			second_document.save()
			revisions.set_user(second_user)
			revisions.set_comment('test version')

		autosave_2 = baker.make(TemporaryDocumentText, document=second_document, author=second_user)
		autosave_3 = baker.make(TemporaryDocumentText, document=self.document, author=second_user)

		response = self.app.get(
			reverse(self.document.get_edit_url_name(), args=[self.document.url_title]) + "?restore={}".format(autosave_2.id),
			user=self.user,
			expect_errors=True,
		)
		self.assertEqual(response.status_code, 400)

		response = self.app.get(
			reverse(self.document.get_edit_url_name(), args=[self.document.url_title]) + "?restore={}".format(autosave_3.id),
			user=self.user,
			expect_errors=True,
		)
		self.assertEqual(response.status_code, 400)

	def test_multiple_autosaves_while_editing(self):
		assign_perm(self.document.edit_permission_name, self.group, self.document)
		baker.make(TemporaryDocumentText, document=self.document, author=self.user, _quantity=2)

		response = self.app.get(reverse(self.document.get_edit_url_name(), args=[self.document.url_title]), user=self.user)
		self.assertEqual(response.status_code, 200)
		self.assertIn("The text of this document was autosaved on", response.body.decode('utf-8'))

	def test_restore_one_of_multiple_autosaves(self):
		assign_perm(self.document.edit_permission_name, self.group, self.document)
		autosave = baker.make(TemporaryDocumentText, document=self.document, author=self.user)
		second_user = baker.make(UserProfile)
		baker.make(TemporaryDocumentText, document=self.document, author=second_user)

		response = self.app.get(
			reverse(self.document.get_edit_url_name(), args=[self.document.url_title]) + "?restore={}".format(autosave.id),
			user=self.user
		)
		self.assertEqual(response.status_code, 200)
		self.assertIn(autosave.text_en, response.body.decode('utf-8'))

	def test_autosave_with_multiple_autosaves(self):
		assign_perm(self.document.edit_permission_name, self.group, self.document)
		baker.make(TemporaryDocumentText, document=self.document, author=self.user)
		second_user = baker.make(UserProfile)
		baker.make(TemporaryDocumentText, document=self.document, author=second_user)

		response = self.app.post(
			reverse('documents:autosave', args=[self.document.url_title]),
			params={'text_en': 'AUTO', 'title_en': self.document.title_en, 'comment': ''},
			user=self.user,
			xhr=True,
		)

		latest_autosave = TemporaryDocumentText.objects.filter(document=self.document).latest('created')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(latest_autosave.text_en, 'AUTO')

	def test_autosaves_removed_after_successful_edit(self):
		assign_perm(self.document.edit_permission_name, self.group, self.document)
		baker.make(TemporaryDocumentText, document=self.document, author=self.user, _quantity=2)

		self.assertEqual(TemporaryDocumentText.objects.count(), 2)

		response = self.app.get(reverse(self.document.get_edit_url_name(), args=[self.document.url_title]), user=self.user)
		form = response.forms['document-form']
		form['title_en'] = 'new title'

		response = form.submit().follow()
		self.assertEqual(response.status_code, 200)
		self.assertEqual(TemporaryDocumentText.objects.count(), 0)

	def test_autosave_url_title_prefix_exists(self):
		for sub_class in Document.__subclasses__():
			response = self.app.get(reverse('documents:create', args=[sub_class.__name__.lower()]), user=self.user)
			self.assertEqual(response.status_code, 200)

			form = response.forms['document-form']
			# we need to scrape the url_title from the action as we can not get it from the url_title field in the form
			url_title = re.search(r'/(?P<url_title>temp_.+)/', form.action).group('url_title')

			# autosave AUTO
			response = self.app.post(
				reverse('documents:autosave', args=[url_title]),
				params={'text_en': 'AUTO', 'title_en': form.get('title_en').value, 'comment': '', 'group': baker.make(Group)},
				xhr=True
			)
			self.assertEqual(response.status_code, 200)
			self.assertEqual(TemporaryDocumentText.objects.count(), 1)
			temporary_document_text = TemporaryDocumentText.objects.get()
			self.assertIn('temp_', temporary_document_text.document.url_title)
			temporary_document_text.delete()

	def test_autosave_url_title_prefix_removed_on_save(self):
		assign_perm("information_pages.add_informationdocument", self.group)
		assign_perm("minutes.add_minutesdocument", self.group)
		assign_perm("polls.add_poll", self.group)

		for sub_class in Document.__subclasses__():
			response = self.app.get(reverse('documents:create', args=[sub_class.__name__.lower()]), user=self.user)
			self.assertEqual(response.status_code, 200)
			form = response.forms['document-form']
			# we need to scrape the url_title from the action as we can not get it from the url_title field in the form
			url_title = re.search(r'/(?P<url_title>temp_.+)/', form.action).group('url_title')

			# autosave AUTO
			response = self.app.post(
				reverse('documents:autosave', args=[url_title]),
				params={'text_en': 'AUTO', 'title_en': form.get('title_en').value, 'comment': ''},
				xhr=True
			)
			self.assertEqual(response.status_code, 200)

			self.assertEqual(TemporaryDocumentText.objects.count(), 1)
			temporary_document_text = TemporaryDocumentText.objects.get()
			self.assertIn('temp_', temporary_document_text.document.url_title)

			self.submit_document_form(form, sub_class)

			self.assertEqual(TemporaryDocumentText.objects.count(), 0)
			temp_prefix_len = re.search(r'temp_\d+_', url_title).end()
			self.assertNotIn('temp_', Document.objects.get(url_title=url_title[temp_prefix_len:]).url_title)

	def submit_document_form(self, form, sub_class):
		text = 'Lorem Ipsum'
		for field_name in form.fields.keys():
			if field_name is not None and 'text' in field_name:
				form.set(field_name, text)
		form.set('comment', text)
		form.set('group', self.group.pk)
		if sub_class == MinutesDocument:
			participants_field = form.get('participants')
			participants_field.select_multiple([participants_field.options[0][0]])
		response = form.submit().follow()
		self.assertEqual(response.status_code, 200)

	def test_autosave_url_title_correct_count_on_save(self):
		assign_perm("information_pages.add_informationdocument", self.group)
		assign_perm("minutes.add_minutesdocument", self.group)
		assign_perm("polls.add_poll", self.group)

		# create document with appended '_\d+' for testing a special case of url_title handling
		baker.make(InformationDocument, url_title=InformationDocument.__name__.lower())
		test_document = baker.make(InformationDocument, url_title="{}_2".format(InformationDocument.__name__.lower()))

		self.assertEqual(
			test_document.generate_default_slug(test_document.url_title),
			"{}_3".format(InformationDocument.__name__.lower()),
		)

	def test_autosave_delete_no_post_request(self):
		baker.make(TemporaryDocumentText, document=self.document, author=self.user)
		response = self.app.get(
			reverse("documents:delete_autosave", args=[self.document.url_title]),
			user=self.user,
			expect_errors=True
		)
		self.assertEqual(response.status_code, 404)

	def test_autosave_delete_non_existing_document(self):
		autosave = baker.make(TemporaryDocumentText, document=self.document, author=self.user)
		response = self.app.post(
			reverse("documents:delete_autosave", args=["non_existing_document"]),
			user=self.user,
			expect_errors=True,
			params={"autosave_id": autosave.id}
		)
		self.assertEqual(response.status_code, 404)

	def test_autosave_delete_user_different_user(self):
		autosave = baker.make(TemporaryDocumentText, document=self.document, author=self.user)
		user = baker.make(UserProfile)
		response = self.app.post(
			reverse("documents:delete_autosave", args=[self.document.url_title]),
			user=user,
			expect_errors=True,
			params={"autosave_id": autosave.id}
		)
		self.assertEqual(response.status_code, 403)

	def test_autosave_delete_user_insufficient_permissions(self):
		user = baker.make(UserProfile)
		autosave = baker.make(TemporaryDocumentText, document=self.document, author=user)

		user2 = baker.make(UserProfile)
		response = self.app.post(
			reverse("documents:delete_autosave", args=[self.document.url_title]),
			user=user2,
			expect_errors=True,
			params={"autosave_id": autosave.id}
		)
		self.assertEqual(response.status_code, 403)

	def test_autosave_can_be_deleted(self):
		user = baker.make(UserProfile)
		autosave = baker.make(TemporaryDocumentText, document=self.document, author=user)
		response = self.app.post(
			reverse("documents:delete_autosave", args=[self.document.url_title]),
			user=user,
			expect_errors=True,
			params={"autosave_id": autosave.id}
		)
		self.assertEqual(response.status_code, 302)
		self.assertEqual(TemporaryDocumentText.objects.count(), 0)

	def test_autosave_delete_not_existing_autosave_id(self):
		baker.make(TemporaryDocumentText, document=self.document, author=self.user)
		response = self.app.post(
			reverse("documents:delete_autosave", args=[self.document.url_title]),
			user=self.user,
			expect_errors=True,
			params={"autosave_id": 400}
		)
		self.assertEqual(response.status_code, 404)

	def test_autosave_delete_autosave_not_created_by_user(self):
		autosave = baker.make(TemporaryDocumentText, document=self.document, author=self.user)
		user = baker.make(UserProfile)
		assign_perm(self.document.edit_permission_name, user, self.document)
		response = self.app.post(
			reverse("documents:delete_autosave", args=[self.document.url_title]),
			user=user,
			expect_errors=True,
			params={"autosave_id": autosave.id}
		)
		self.assertEqual(response.status_code, 400)

	def test_autosave_delete_document_is_in_creation(self):
		autosave = baker.make(TemporaryDocumentText, document=self.document, author=self.user)
		response = self.app.post(
			reverse("documents:delete_autosave", args=[self.document.url_title]),
			user=self.user,
			params={"autosave_id": autosave.id}
		)
		self.assertEqual(response.status_code, 302)
		self.assertRedirects(response, reverse("index"))
		self.assertEqual(TemporaryDocumentText.objects.count(), 0)
		self.assertEqual(Document.objects.count(), 0)

	def test_autosave_delete_document_not_in_creation(self):
		autosave = baker.make(TemporaryDocumentText, document=self.document, author=self.user)
		assign_perm(self.document.edit_permission_name, self.group, self.document)
		response = self.app.post(
			reverse("documents:delete_autosave", args=[self.document.url_title]),
			user=self.user,
			params={"autosave_id": autosave.id}
		)
		self.assertEqual(response.status_code, 302)
		self.assertRedirects(response, reverse("edit", args=[self.document.url_title]))
		self.assertEqual(TemporaryDocumentText.objects.count(), 0)
		self.assertEqual(Document.objects.count(), 1)


class TestMarkdownRendering(WebTest):
	csrf_checks = False

	@classmethod
	def setUpTestData(cls):
		cls.user = baker.make(UserProfile, is_superuser=True)
		cls.document_text = 'test'
		cls.document = baker.make(InformationDocument, text_en=cls.document_text)
		cls.document.set_all_permissions(baker.make(Group))

	def test_render_text_no_permission(self):
		user_without_permission = baker.make(UserProfile)
		response = self.app.post(
			reverse('documents:render', args=[self.document.url_title]),
			params={'text': self.document_text},
			xhr=True,
			expect_errors=True,
			user=user_without_permission
		)
		self.assertEqual(response.status_code, 403)

	def test_render_text_wrong_method(self):
		response = self.app.get(
			reverse('documents:render', args=[self.document.url_title]),
			params={'text': self.document_text},
			user=self.user,
			xhr=True,
			expect_errors=True
		)
		self.assertEqual(response.status_code, 400)

	def test_render_text(self):
		response = self.app.post(
			reverse('documents:render', args=[self.document.url_title]),
			params={'text': self.document_text},
			user=self.user,
			xhr=True
		)
		self.assertEqual(response.status_code, 200)
		self.assertEqual('<p>' + self.document_text + '</p>', response.body.decode('utf-8'))


class TestLanguage(WebTest):
	csrf_checks = False

	@classmethod
	def setUpTestData(cls):
		cls.user = baker.make(UserProfile, is_superuser=True)
		cls.document_text = 'test'
		cls.document = baker.make(InformationDocument, text_de=cls.document_text)
		cls.document.set_all_permissions(baker.make(Group))

		cls.empty_document = baker.make(InformationDocument)
		cls.empty_document.set_all_permissions(baker.make(Group))

	# Test that alert is there if only one language available
	# Test no alert if both languages missing
	def test_not_available_alert(self):
		response = self.app.post(reverse('set_lang'), params={'language': 'en'}, user=self.user)
		self.assertEqual(response.status_code, 302)

		response = self.app.get(reverse('view', args=[self.document.url_title]), user=self.user)
		self.assertEqual(response.status_code, 200)
		messages = list(response.context['messages'])
		self.assertEqual(len(messages), 1)
		self.assertEqual(str(messages[0]), 'The requested document is not available in the selected language. It will be shown in the available language instead.')

		response = self.app.post(reverse('set_lang'), params={'language': 'de'}, user=self.user)
		self.assertEqual(response.status_code, 302)

		response = self.app.get(reverse('view', args=[self.document.url_title]), user=self.user)
		self.assertEqual(response.status_code, 200)
		messages = list(response.context['messages'])
		self.assertEqual(len(messages), 0)

	def test_no_not_available_alert_on_empty_document(self):
		response = self.app.post(reverse('set_lang'), params={'language': 'en'}, user=self.user)
		self.assertEqual(response.status_code, 302)

		response = self.app.get(reverse('view', args=[self.empty_document.url_title]), user=self.user)
		self.assertEqual(response.status_code, 200)
		messages = list(response.context['messages'])
		self.assertEqual(len(messages), 0)


class TestSignals(TestCase):
	@classmethod
	def setUpTestData(cls):
		cls.user = baker.make(UserProfile, is_superuser=True)

	def test_slugify_hook(self):
		# create a new document for every subclass of document
		# and see whether the url_title is automatically created
		for obj_id, subclass in enumerate(Document.__subclasses__()):
			new_document = baker.make(subclass, title_en="test_{}".format(obj_id), url_title="")
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
			test_object = baker.make(subclass, title_en="test")
			user_permissions = get_perms(group, test_object)
			self.assertNotEqual(len(user_permissions), 0)

			for permission in group.permissions.all():
				self.assertIn(permission.codename, user_permissions)

	def test_possibility_to_change_permission_for_groups(self):
		group = baker.make(Group, name="FSR")
		test_user = baker.make(UserProfile)
		test_user.groups.add(group)
		test_user.save()

		model_permissions = get_perms_for_model(InformationDocument)
		permission_names = []
		for permission in model_permissions:
			permission_name = "{}.{}".format(permission.content_type.app_label, permission.codename)
			assign_perm(permission_name, group)
			permission_names.append(permission_name)

		# test whether we can remove a permission from the group
		# the permission should not be added again
		test_object = baker.make(InformationDocument)
		self.assertTrue(test_user.has_perm(permission_names[0], test_object))
		remove_perm(permission_names[0], group, test_object)
		test_object.save()
		self.assertFalse(test_user.has_perm(permission_names[0], test_object))


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
			self.assertIsNot(subclass.get_view_url, Document.get_view_url, msg=msg)

	def test_view_permissions(self):
		for subclass in Document.__subclasses__():
			if self.is_abstract_model(subclass):
				continue

			self.assertTrue(self.has_permissions(subclass), msg="All Document subclasses must specify permissions in their Meta class")
			self.assertTrue(hasattr(subclass, "VIEW_PERMISSION_NAME"), msg="All Document subclasses must specify a VIEW_PERMISSION_NAME field")


class TestAttachments(WebTest):
	"""
		Tests creating, viewing and deleting attachments
		InformationDocuments are used as testclass. It is assumed that the behavior is similar with other documenttypes
	"""
	csrf_checks = False

	@classmethod
	def setUpTestData(cls):
		cls.user = baker.make(UserProfile, is_superuser=True)

		cls.group = baker.make(Group, make_m2m=True)
		for permission in get_perms_for_model(InformationDocument):
			permission_name = "{}.{}".format(permission.content_type.app_label, permission.codename)
			assign_perm(permission_name, cls.group)
		cls.group.save()

		cls.group_user = baker.make(UserProfile)
		cls.group_user.groups.add(cls.group)
		cls.group_user.save()

		cls.document = baker.make(InformationDocument)

	def setUp(self):
		self.content = "test content of test attachment"
		attachment_file = ContentFile(self.content)
		self.attachment = baker.make(Attachment, document=self.document, displayname="test")  # displayname does not include the extension
		self.attachment.file.save('temp.txt', attachment_file)
		self.attachment.save()

	def tearDown(self):
		for attachment in self.document.attachments.all():
			attachment.file.delete()
		self.attachment.file.delete()

	def test_view_attachment_overview_page(self):
		response = self.app.get(reverse(self.document.get_attachments_url_name(), args=[self.document.url_title]), user=self.user)
		self.assertEqual(response.status_code, 200)

		# there should be our attachment
		self.assertIn(self.attachment.displayname, response.body.decode('utf-8'))

		# there should be no toc
		self.assertNotIn("toc d-print-none", response.body.decode('utf-8'))

	def test_create_attachment(self):
		upload_files = [
			('file', 'test.txt', bytes(tempfile.SpooledTemporaryFile(max_size=10000, prefix='txt', mode='r')))
		]

		# test that user who has no change permission on a document can not add an attachment
		# and neither see the corresponding page
		normal_user = baker.make(UserProfile)

		response = self.app.get(
			reverse(self.document.get_attachments_url_name(), args=[self.document.url_title]),
			user=normal_user,
			expect_errors=True
		)
		self.assertEqual(response.status_code, 403)

		response = self.app.post(
			reverse(self.document.get_attachments_url_name(), args=[self.document.url_title]),
			content_type='multipart/form-data',
			upload_files=upload_files,
			user=normal_user,
			expect_errors=True
		)
		self.assertEqual(response.status_code, 403)

		# test that user who is allowed to view the document may not add attachments to it
		# and neither see the corresponding page
		assign_perm("view_informationdocument", normal_user, self.document)

		response = self.app.get(
			reverse(self.document.get_attachments_url_name(), args=[self.document.url_title]),
			user=normal_user,
			expect_errors=True
		)
		self.assertEqual(response.status_code, 403)

		response = self.app.post(
			reverse(self.document.get_attachments_url_name(), args=[self.document.url_title]),
			content_type='multipart/form-data',
			upload_files=upload_files,
			user=normal_user,
			expect_errors=True
		)
		self.assertEqual(response.status_code, 403)

		# test that member of group who has according permissions is allowed to upload attachments
		# and to see the corresponding page
		response = self.app.get(reverse(self.document.get_attachments_url_name(), args=[self.document.url_title]), user=self.group_user)
		self.assertEqual(response.status_code, 200)

		response = self.app.post(
			reverse(self.document.get_attachments_url_name(), args=[self.document.url_title]),
			content_type='multipart/form-data',
			upload_files=upload_files,
			user=self.group_user
		)
		self.assertEqual(response.status_code, 200)

		# test that superuser is allowed to upload attachments and to see the corresponding page
		response = self.app.get(reverse(self.document.get_attachments_url_name(), args=[self.document.url_title]), user=self.user)
		self.assertEqual(response.status_code, 200)

		response = self.app.post(
			reverse(self.document.get_attachments_url_name(), args=[self.document.url_title]),
			content_type='multipart/form-data',
			upload_files=upload_files,
			user=self.user
		)
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
		self.assertEqual(response.status_code, 403)

		# try to delete an attachment as user with no permissions
		normal_user = baker.make(UserProfile)
		response = self.app.post(reverse('documents:delete_attachment'), params=params, expect_errors=True, xhr=True, user=normal_user)
		self.assertEqual(
			response.status_code,
			403,
			msg="If users have no permissions they should not be able to delete an attachment"
		)

		# try to delete an attachment as user with wrong permissions
		assign_perm(InformationDocument.get_view_permission(), normal_user, self.document)
		response = self.app.post(reverse('documents:delete_attachment'), params=params, expect_errors=True, xhr=True, user=normal_user)
		self.assertEqual(
			response.status_code,
			403,
			msg="If users has no permissions they should not be able to delete an attachment"
		)

		# try to delete an attachment as user with correct permissions
		response = self.app.post(reverse('documents:delete_attachment'), params=params, xhr=True, user=self.group_user)
		self.assertEqual(
			response.status_code,
			200,
			msg="Users with the correct permissions for a document should be able to delete an attachment"
		)

		# re create the attachment
		self.attachment.save()

		# try to delete an attachment as superuser
		response = self.app.post(reverse('documents:delete_attachment'), params=params, xhr=True, user=self.user)
		self.assertEqual(
			response.status_code,
			200,
			msg="Users with the correct permissions for a document should be able to delete an attachment"
		)

	def test_view_attachment(self):
		params = {
			'hash_value': self.attachment.hash_value,
		}

		# test that a user with insufficient permissions is not allowed to view/download an attachment
		# be an anonymous user
		response = self.app.post(reverse('documents:download_attachment'), params=params, expect_errors=True)
		self.assertEqual(response.status_code, 405, msg="Should be Method not allowed as user used wrong request method")

		response = self.app.get(reverse('documents:download_attachment'), params=params, expect_errors=True)
		self.assertEqual(response.status_code, 302)
		response = response.follow()
		self.assertTemplateUsed(response, 'login.html', msg_prefix="Anonymous users should see the login page")

		# test viewing an attachment using a user with insufficient permissions
		normal_user = baker.make(UserProfile)
		assign_perm('change_informationdocument', normal_user, self.document)

		response = self.app.get(reverse('documents:download_attachment'), params=params, expect_errors=True, user=normal_user)
		self.assertEqual(response.status_code, 403, msg="Should be forbidden as user has insufficient permissions")

		# grant the correct permission to the user an try again
		assign_perm(InformationDocument.get_view_permission(), normal_user, self.document)

		response = self.app.get(reverse('documents:download_attachment'), params=params, user=normal_user)
		self.assertEqual(
			response.status_code,
			200,
			msg="Users with sufficient permissions should be able to download an attachment"
		)
		self.assertEqual(
			response.body.decode('utf-8'),
			self.content,
			msg="An attachment that has been downloaded should contain its original content"
		)
		self.assertEqual(
			response.headers['Content-Disposition'],
			"attachment; filename=\"b\'test.txt\'\"; filename*=UTF-8\'\'test.txt",
			msg="The filename should include the file extension although not included in the displayname"
		)

		# try the same with a user that is in a group having the correct permission
		response = self.app.get(reverse('documents:download_attachment'), params=params, user=self.group_user)
		self.assertEqual(
			response.status_code,
			200,
			msg="Users with sufficient permissions should be able to download an attachment"
		)
		self.assertEqual(
			response.body.decode('utf-8'),
			self.content,
			msg="An attachment that has been downloaded should contain its original content"
		)

		# make sure that a superuser is always allowed to download an attachment
		response = self.app.get(reverse('documents:download_attachment'), params=params, user=self.user)
		self.assertEqual(
			response.status_code,
			200,
			msg="Users with sufficient permissions should be able to download an attachment"
		)
		self.assertEqual(
			response.body.decode('utf-8'),
			self.content,
			msg="An attachment that has been downloaded should contain its original content"
		)

	def test_sort_attachments(self):
		baker.make(Attachment, _quantity=3, document=self.document)

		attachments = Attachment.objects.all()
		old_attachment_order = {}
		for index, attachment in enumerate(attachments):
			self.assertEqual(attachment.index, 0)
			attachment.index = index
			attachment.save()
			old_attachment_order[attachment.id] = index

		# reverse ordering of attachments
		attachments = Attachment.objects.all().order_by('-index')
		new_attachment_order = {}
		for index, attachment in enumerate(attachments):
			new_attachment_order[attachment.id] = index

		response = self.app.post(
			reverse('documents:update_attachment_order'),
			params=new_attachment_order,
			xhr=True,
			user=self.user,
		)
		self.assertEqual(response.status_code, 200)

		# check that all indices changed
		attachments = Attachment.objects.all().order_by('index')
		for attachment in attachments:
			self.assertNotEqual(
				attachment.index,
				old_attachment_order[attachment.id],
				msg="Old id and new id should not be the same",
			)

	def test_attachment_change_no_direct_download(self):
		self.assertFalse(self.attachment.no_direct_download, "attachments can be downloaded directly by default")
		response = self.app.post(
			reverse('documents:change_attachment'),
			params={'id': self.attachment.id, 'no_direct_download': 'false'},
			user=self.user,
			xhr=True,
		)
		self.assertEqual(response.status_code, 200, "it should be possible to change the direct download state")
		attachment = Attachment.objects.get(pk=self.attachment.id)
		self.assertFalse(attachment.no_direct_download)

	def test_attachment_change_no_direct_download_wrong_permissions(self):
		self.assertFalse(self.attachment.no_direct_download)
		user = baker.make(UserProfile)
		response = self.app.post(
			reverse('documents:change_attachment'),
			params={'id': self.attachment.id, 'no_direct_download': 'false'},
			user=user,
			xhr=True,
			expect_errors=True
		)
		self.assertEqual(response.status_code, 403)

	def test_attachment_change_no_direct_download_wrong_request_type(self):
		response = self.app.get(
			reverse('documents:change_attachment'),
			params={'id': self.attachment.id, 'no_direct_download': 'false'},
			user=self.user,
			xhr=True,
			expect_errors=True,
		)
		self.assertEqual(response.status_code, 404)

	def test_attachment_change_no_direct_download_no_ajax(self):
		response = self.app.post(
			reverse('documents:change_attachment'),
			params={'id': self.attachment.id, 'no_direct_download': 'false'},
			user=self.user,
			expect_errors=True,
		)
		self.assertEqual(response.status_code, 404)

	def test_attachment_change_displayname(self):
		new_displayname = 'lorem ipsum'
		response = self.app.post(
			reverse('documents:change_attachment'),
			params={'id': self.attachment.id, 'displayname': new_displayname},
			user=self.user,
			xhr=True,
		)
		self.assertEqual(response.status_code, 200, "it should be possible to change displayname")
		attachment = Attachment.objects.get(pk=self.attachment.id)
		self.assertEqual(attachment.displayname, new_displayname)

	def test_attachment_change_displayname_permissions(self):
		self.assertFalse(self.attachment.no_direct_download)
		user = baker.make(UserProfile)
		new_displayname = 'lorem ipsum'
		response = self.app.post(
			reverse('documents:change_attachment'),
			params={'id': self.attachment.id, 'displayname': new_displayname},
			user=user,
			xhr=True,
			expect_errors=True
		)
		self.assertEqual(response.status_code, 403)

	def test_attachment_change_displayname_wrong_request_type(self):
		new_displayname = 'lorem ipsum'
		response = self.app.get(
			reverse('documents:change_attachment'),
			params={'id': self.attachment.id, 'displayname': new_displayname},
			user=self.user,
			xhr=True,
			expect_errors=True,
		)
		self.assertEqual(response.status_code, 404)

	def test_attachment_change_attachment_no_ajax(self):
		new_displayname = 'lorem ipsum'
		response = self.app.post(
			reverse('documents:change_attachment'),
			params={'id': self.attachment.id, 'displayname': new_displayname},
			user=self.user,
			expect_errors=True,
		)
		self.assertEqual(response.status_code, 404)

	def test_attachment_change_no_direct_download_view(self):
		attachment = baker.make(Attachment, document=self.document, displayname="pic.jpg", no_direct_download=True)
		response = self.app.get(
			reverse(self.document.get_view_url_name(), args=[self.document.url_title]),
			user=self.user,
		)
		self.assertEqual(response.status_code, 200)
		self.assertNotIn(attachment.displayname, response.body.decode('utf-8'))

	def test_attachment_get_all_attachments_no_images(self):
		response = self.app.get(
			reverse('documents:get_attachments', args=[self.document.id]),
			user=self.user,
			xhr=True,
		)
		self.assertEqual(response.status_code, 200)
		returned_data = json.loads(response.body.decode('utf-8'))
		self.assertEqual(len(returned_data), 0)

	def test_attachment_get_all_attachments(self):
		attachment = baker.make(Attachment, displayname="pic.jpg", document=self.document)
		attachment.save()

		response = self.app.get(
			reverse('documents:get_attachments', args=[self.document.id]),
			user=self.user,
			xhr=True,
		)
		self.assertEqual(response.status_code, 200)
		returned_data = json.loads(response.body.decode('utf-8'))
		self.assertEqual(len(returned_data), 1)

	def test_attachment_get_all_attachments_wrong_user(self):
		user = baker.make(UserProfile)
		response = self.app.get(
			reverse('documents:get_attachments', args=[self.document.id]),
			user=user,
			xhr=True,
			expect_errors=True,
		)
		self.assertEqual(response.status_code, 403)

	def test_attachment_get_all_attachments_no_ajax(self):
		response = self.app.get(
			reverse('documents:get_attachments', args=[self.document.id]),
			user=self.user,
			expect_errors=True,
		)
		self.assertEqual(response.status_code, 404)

	def test_attachment_get_all_attachments_no_document_id(self):
		response = self.app.get(
			reverse('documents:get_attachments', args=[self.document.id]),
			user=self.user,
			expect_errors=True,
		)
		self.assertEqual(response.status_code, 404)

	def test_create_attachment_from_editor_wrong_method(self):
		response = self.app.get(
			reverse('documents:create_attachment'),
			user=self.user,
			expect_errors=True,
		)
		self.assertEqual(response.status_code, 404)

	def test_create_attachment_from_editor_no_permission(self):
		params = {
			'document': self.document.id,
		}

		normal_user = baker.make(UserProfile)

		response = self.app.post(
			reverse('documents:create_attachment'),
			params=params,
			user=normal_user,
			xhr=True,
			expect_errors=True
		)
		self.assertEqual(response.status_code, 403)

	def test_create_attachment_from_editor_invalid_form(self):
		upload_files = [
			('file', 'test.txt', bytes())
		]

		params = {
			'no_direct_download': True,
			'document': self.document.id,
			'displayname': '',
		}

		response = self.app.post(
			reverse('documents:create_attachment'),
			content_type='multipart/form-data',
			upload_files=upload_files,
			params=params,
			user=self.user,
			xhr=True,
			expect_errors=True
		)
		self.assertEqual(response.status_code, 400)

	def test_create_attachment_from_editor(self):
		upload_files = [
			('file', 'test.txt', bytes("Test content of file", encoding='utf-8'))
		]

		params = {
			'no_direct_download': True,
			'document': self.document.id,
			'displayname': '',
		}

		self.assertEqual(Attachment.objects.count(), 1)
		self.assertEqual(self.document.attachments.count(), 1)

		response = self.app.post(
			reverse('documents:create_attachment'),
			content_type='multipart/form-data',
			upload_files=upload_files,
			params=params,
			user=self.user,
			xhr=True,
		)
		self.assertEqual(response.status_code, 200)

		self.assertEqual(Attachment.objects.count(), 2)
		self.assertEqual(self.document.attachments.count(), 2)
		self.assertEqual(self.document.attachments.last().index, 2)

	def test_attachments_download_without_parameter(self):
		response = self.app.get(reverse("documents:download_attachment"), user=self.user, expect_errors=True)
		self.assertEqual(response.status_code, 404)


class TestDeletion(WebTest):
	csrf_checks = False

	@classmethod
	def setUpTestData(cls):
		cls.user = baker.make(UserProfile, is_superuser=True)
		cls.user.groups.add(Group.objects.get(name=settings.STAFF_GROUP_NAME))
		cls.document = baker.make(
			InformationDocument,
			title_en='title'
		)
		cls.document.set_all_permissions(baker.make(Group))

	def test_delete_cascade(self):
		response = self.app.get(reverse("documents:get_delete_cascade", args=[self.document.url_title]), user=self.user)
		self.assertEqual(response.status_code, 200)
		data = json.loads(response.body.decode('utf-8'))
		self.assertEqual(type(self.document).__name__, data[0]["type"])

	def test_delete_cascade_nested_objects(self):
		baker.make(Attachment, document=self.document)
		response = self.app.get(reverse("documents:get_delete_cascade", args=[self.document.url_title]), user=self.user)
		self.assertEqual(response.status_code, 200)
		data = json.loads(response.body.decode('utf-8'))
		self.assertEqual(len(data), 2)
		self.assertEqual(Attachment.__name__, data[1][0]['type'])

	def test_delete_cascade_no_permissions(self):
		user = baker.make(UserProfile)
		response = self.app.get(reverse("documents:get_delete_cascade", args=[self.document.url_title]), user=user, expect_errors=True)
		self.assertEqual(response.status_code, 403)

	def test_delete_documents(self):
		for document_class in Document.__subclasses__():
			document = baker.make(document_class)
			self.assertEqual(Document.objects.count(), 2)
			response = self.app.post(reverse("documents:delete_document", args=[document.url_title]), user=self.user)
			self.assertEqual(response.status_code, 200)
			self.assertEqual(Document.objects.count(), 1)

	def test_delete_documents_with_attachment(self):
		for document_class in Document.__subclasses__():
			document = baker.make(document_class)
			self.assertEqual(Document.objects.count(), 2)
			baker.make(Attachment, document=document)
			self.assertEqual(Attachment.objects.count(), 1)
			response = self.app.post(reverse("documents:delete_document", args=[document.url_title]), user=self.user)
			self.assertEqual(response.status_code, 200)
			self.assertEqual(Attachment.objects.count(), 0)
			self.assertEqual(Document.objects.count(), 1)

	def test_delete_documents_insufficient_permissions(self):
		user = baker.make(UserProfile)
		for document_class in Document.__subclasses__():
			document = baker.make(document_class)
			self.assertEqual(Document.objects.count(), 2)
			response = self.app.post(reverse("documents:delete_document", args=[document.url_title]), user=user, expect_errors=True)
			self.assertEqual(response.status_code, 403)
			self.assertEqual(Document.objects.count(), 2)
			document.delete()

	def test_delete_button_not_present_if_creating_document(self):
		# test that the delete button is not visible if the document that gets edited has no revisions
		response = self.app.get(reverse(self.document.get_edit_url_name(), args=[self.document.url_title]), user=self.user)
		self.assertEqual(response.status_code, 200)
		self.assertNotIn("deleteDocumentButton", response.body.decode('utf-8'))

	def test_discard_button_if_creating_document(self):
		# test that the discard button exists if the document that gets edited has no revisions or autosaves
		response = self.app.get(reverse(self.document.get_edit_url_name(), args=[self.document.url_title]), user=self.user)
		self.assertEqual(response.status_code, 200)
		self.assertIn("discardDocumentButton", response.body.decode('utf-8'))

	def test_delete_button_present_if_editing_already_existing_document(self):
		# test that the delete button is visible if the document has at least one revision
		response = self.app.get(reverse(self.document.get_edit_url_name(), args=[self.document.url_title]), user=self.user)

		form = response.forms['document-form']
		form['comment'] = 'new revision'
		response = form.submit().follow()
		self.assertEqual(response.status_code, 200)

		response = self.app.get(reverse(self.document.get_edit_url_name(), args=[self.document.url_title]), user=self.user)
		self.assertEqual(response.status_code, 200)
		self.assertIn("deleteDocumentButton", response.body.decode('utf-8'))

	def test_delete_document_in_creation_fails_without_autosave(self):
		user = baker.make(UserProfile)
		document = baker.make(InformationDocument)
		self.assertEqual(Document.objects.count(), 2)
		response = self.app.post(reverse("documents:delete_document", args=[document.url_title]), user=user, expect_errors=True)
		self.assertEqual(response.status_code, 403)

	def test_delete_document_in_creation_with_autosave(self):
		user = baker.make(UserProfile)
		document = baker.make(InformationDocument)
		self.assertEqual(Document.objects.count(), 2)
		baker.make(TemporaryDocumentText, document=document, author=user)
		self.assertEqual(TemporaryDocumentText.objects.count(), 1)
		response = self.app.post(reverse("documents:delete_document", args=[document.url_title]), user=user)
		self.assertEqual(response.status_code, 200)
		self.assertEqual(Document.objects.count(), 1)
		self.assertEqual(TemporaryDocumentText.objects.count(), 0)


class TestPreview(WebTest):
	csrf_checks = False

	@classmethod
	def setUpTestData(cls):
		cls.document = baker.make(Document)
		cls.user = baker.make(UserProfile, is_superuser=True)

	def test_preview_wrong_method(self):
		response = self.app.post(reverse('documents:preview') + '?hash_value={}'.format(self.document.hash_value), status=404)
		self.assertEqual(response.status_code, 404)

	def test_preview_document_does_not_exist(self):
		response = self.app.get(reverse('documents:preview') + '?hash_value={}'.format(1), status=404)
		self.assertEqual(response.status_code, 404)

	def test_preview_without_get_param(self):
		response = self.app.get(reverse('documents:preview'), status=404)
		self.assertEqual(response.status_code, 404)

	def test_preview_view(self):
		response = self.app.get(reverse('documents:preview') + '?hash_value={}'.format(self.document.hash_value))
		self.assertEqual(response.status_code, 200)

		self.assertIn(self.document.text, response.body.decode('utf-8'))

		preview_url = '/ws/preview'
		with self.settings(PREVIEW_URL=preview_url):
			self.assertIn(preview_url, response.body.decode('utf-8'))


class TestPermissionOverview(WebTest):
	csrf_checks = False

	@classmethod
	def setUpTestData(cls):
		cls.user = baker.make(UserProfile)
		cls.minutes_document = baker.make(MinutesDocument)
		cls.poll = baker.make(Poll)
		cls.information_document = baker.make(InformationDocument)
		cls.group = baker.make(Group)
		cls.user.groups.add(cls.group)
		cls.minutes_document.set_all_permissions(cls.group)
		cls.poll.set_all_permissions(cls.group)
		cls.information_document.set_all_permissions(cls.group)
		assign_perm("minutes.add_minutesdocument", cls.group)
		assign_perm("polls.add_poll", cls.group)
		assign_perm("information_pages.add_informationdocument", cls.group)

		cls.anonymous_group = Group.objects.get(name=settings.ANONYMOUS_GROUP_NAME)
		cls.university_network_group = Group.objects.get(name=settings.UNIVERSITY_GROUP_NAME)
		cls.student_group = Group.objects.get(name=settings.STUDENT_GROUP_NAME)
		cls.staff_group = Group.objects.get(name=settings.STAFF_GROUP_NAME)

		groups = [cls.anonymous_group, cls.university_network_group, cls.student_group, cls.staff_group]
		cls.documents = [cls.minutes_document, cls.poll, cls.information_document]
		for document in cls.documents:
			for group in groups:
				assign_perm(document.view_permission_name, group, document)
			assign_perm(document.edit_permission_name, cls.staff_group, document)

	def test_permission_display(self):
		"""
		Test if the permissions are correctly shown in the sidebar
		"""
		icons = [
			"fa-globe permission-icon-view",
			"fa-university permission-icon-view",
			"fa-user permission-icon-view",
			"fa-briefcase permission-icon-edit"
		]
		for document in self.documents:
			response = self.app.get(reverse(document.get_edit_url_name(), args=[document.url_title]), user=self.user)
			for icon in icons:
				self.assertIn(icon, response)

	def test_permission_display_2(self):
		"""
		Test if the permissions are correctly shown in the sidebar
		"""
		for document in self.documents:
			remove_perm(document.view_permission_name, self.anonymous_group, document)
			assign_perm(document.edit_permission_name, self.student_group, document)
			remove_perm(document.edit_permission_name, self.staff_group, document)

		icons = [
			"fa-globe permission-icon-none",
			"fa-university permission-icon-view",
			"fa-user permission-icon-edit",
			"fa-briefcase permission-icon-view"
		]
		for document in self.documents:
			response = self.app.get(reverse(document.get_edit_url_name(), args=[document.url_title]), user=self.user)
			for icon in icons:
				self.assertIn(icon, response)


class DocumentCreationTests(WebTest):

	csrf_checks = False

	@classmethod
	def setUpTestData(cls):
		cls.user = baker.make(UserProfile)
		cls.group = baker.make(Group)
		cls.user.groups.add(cls.group)
		assign_perm("information_pages.add_informationdocument", cls.group)
		assign_perm("minutes.add_minutesdocument", cls.group)

		cls.document_types = ['minutesdocument', 'informationdocument']

	def test_create_document_with_one_group(self):
		for document_type in self.document_types:
			response = self.app.get(reverse('documents:create', args=[document_type]), user=self.user)
			self.assertEqual(response.status_code, 200)
			body = response.body.decode('utf-8')
			self.assertIn('type="hidden" name="group"', body)

	def test_create_document_with_two_groups(self):
		group = baker.make(Group)
		self.user.groups.add(group)
		assign_perm("information_pages.add_informationdocument", group)
		assign_perm("minutes.add_minutesdocument", group)

		for document_type in self.document_types:
			response = self.app.get(reverse('documents:create', args=[document_type]), user=self.user)
			self.assertEqual(response.status_code, 200)
			body = response.body.decode('utf-8')
			self.assertNotIn("name=group type=hidden", body, msg="User should have the choice of groups if he is in more than one group, that can create minutes documents")

	def test_create_document_with_no_groups(self):
		for group in Group.objects.all():
			self.user.groups.remove(group)
		self.user.save()

		for document_type in self.document_types:
			response = self.app.get(reverse('documents:create', args=[document_type]), user=self.user, expect_errors=True)
			self.assertEqual(response.status_code, 403)


class ScaledImageExtensionTests(TestCase):

	def setUp(self):
		self.md = markdown.Markdown(
			extensions=[
				'_1327.documents.markdown_scaled_image_extension',
			]
		)
		self.pattern = ScaledImagePattern(SCALED_IMAGE_LINK_RE, self.md)
		self.regex = self.pattern.getCompiledRegExp()

		# Replace this function with a mock stub because the real implementation digs too deep into the system
		self.pattern.unescape = lambda text: text

	def test_scaled_image_regex(self):
		self.assertEqual(None, self.regex.match('![Alt](http://example.com)'))
		self.assertEqual(None, self.regex.match('![Alt](http://example.com 1327)'))
		self.assertEqual(None, self.regex.match('![Alt](http://example.com =1327)'))
		self.assertEqual(None, self.regex.match('![Alt](http://example.com 13x27)'))

		m = self.regex.match('![Alt](http://example.com =13x27)')
		self.assertTrue(m)
		self.assertEqual('Alt', m.group(2))
		self.assertEqual('http://example.com', m.group(9))
		self.assertEqual('13', m.group(11))
		self.assertEqual('27', m.group(12))

		m = self.regex.match('![Alt](<http://example.com now with spaces> =13x27)')
		self.assertTrue(m)
		self.assertEqual('<http://example.com now with spaces>', m.group(9))

		m = self.regex.match('![Alt](http://example.com "Hi I am a title" =13x27)')
		self.assertTrue(m)
		self.assertEqual('http://example.com "Hi I am a title"', m.group(9))

		m = self.regex.match('![Alt](http://example.com =1327x)')
		self.assertTrue(m)
		self.assertEqual('1327', m.group(11))
		self.assertEqual(None, m.group(12))

		m = self.regex.match('![Alt](http://example.com =x1327)')
		self.assertTrue(m)
		self.assertEqual(None, m.group(11))
		self.assertEqual('1327', m.group(12))

	def test_scaled_image_pattern(self):
		el = self.pattern.handleMatch(self.regex.match('![Alt](http://example.com "Hi I am a title" =13x27)'))
		self.assertEqual('img', el.tag)
		self.assertEqual('http://example.com', el.get('src'))
		self.assertEqual('Alt', el.get('alt'))
		self.assertEqual('Hi I am a title', el.get('title'))
		self.assertEqual('13px', el.get('width'))
		self.assertEqual('27px', el.get('height'))

		el = self.pattern.handleMatch(self.regex.match('![Alt](http://example.com "Hi I am a title" =1327x)'))
		self.assertEqual('1327px', el.get('width'))
		self.assertEqual(None, el.get('height'))

		el = self.pattern.handleMatch(self.regex.match('![Alt](http://example.com "Hi I am a title" =x1327)'))
		self.assertEqual(None, el.get('width'))
		self.assertEqual('1327px', el.get('height'))
