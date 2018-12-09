from datetime import datetime
from email.message import EmailMessage
import tempfile
from unittest.mock import MagicMock, mock_open, patch

from bs4 import BeautifulSoup
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import make_aware
from django_webtest import WebTest
from freezegun import freeze_time
from model_mommy import mommy

from _1327.emails import utils
from _1327.emails.forms import QuickSearchForm, SearchForm
from _1327.emails.models import Email


class EmailFormTests(TestCase):
	def test_quicksearch_form(self):
		form = QuickSearchForm(data={})
		self.assertFalse(form.is_valid())

		form = QuickSearchForm(data={'text': 'Stollen'})
		self.assertTrue(form.is_valid())

	def test_search_form(self):
		form = SearchForm(data={})
		self.assertFalse(form.is_valid())

		form = SearchForm(data={'text': 'Stollen'})
		self.assertTrue(form.is_valid())
		self.assertFalse(form.cleaned_data['has_attachments'])

		form = SearchForm(data={'sender': 'Santa Claus'})
		self.assertTrue(form.is_valid())

		form = SearchForm(data={'receiver': 'Santa Claus'})
		self.assertTrue(form.is_valid())

		form = SearchForm(data={'received_before': '2018-12-24'})
		self.assertTrue(form.is_valid())

		form = SearchForm(data={'received_after': '2018-12-24'})
		self.assertTrue(form.is_valid())

		form = SearchForm(data={'has_attachments': True})
		self.assertTrue(form.is_valid())


class EmailModelTest(TestCase):
	def test_to(self):
		email = Email(to_names=[], to_addresses=[])
		self.assertEqual(email.to(), [])
		email = Email(to_names=["a", "b"], to_addresses=["a@a", "b@b"])
		self.assertEqual(email.to(), [("a", "a@a"), ("b", "b@b")])

	def test_cc(self):
		email = Email(cc_names=[], cc_addresses=[])
		self.assertEqual(email.cc(), [])
		email = Email(cc_names=["a", "b"], cc_addresses=["a@a", "b@b"])
		self.assertEqual(email.cc(), [("a", "a@a"), ("b", "b@b")])

	def test_subject_nonempty(self):
		email = Email()
		self.assertGreater(len(email.subject_nonempty()), 0)
		email = Email(subject="Hey Ho")
		self.assertEqual(email.subject_nonempty(), "Hey Ho")

	def test_upload_path(self):
		email = Email(id=1)
		with self.assertRaises(Exception):
			email.envelope.field.upload_to(email, "ignored-filename")

		email = Email(date=make_aware(datetime.now()))
		with self.assertRaises(Exception):
			email.envelope.field.upload_to(email, "ignored-filename")

		email = Email(id=42, date=datetime(2018, 12, 12))
		path = email.envelope.field.upload_to(email, "ignored-filename")
		self.assertEqual(path, "emails/2018/12/42.eml")


class EmailUtilsTest(TestCase):
	def test_email_from_bytes(self):
		email = utils.email_from_bytes(b"""\
From: Orange Sheep <orange.sheep@world>

I like grass.
""")

		self.assertEqual(email['From'], "Orange Sheep <orange.sheep@world>")

	def test_get_raw_email_for_email_entity(self):
		raw = b"""\
From: Orange Sheep <orange.sheep@world>

I like grass.
"""

		with patch("builtins.open", mock_open(read_data=raw)) as mock_file:
			email = MagicMock()
			email.envelope.path.return_value = "email.eml"
			self.assertEqual(utils.get_raw_email_for_email_entity(email), raw)
			mock_file.assert_called_with(email.envelope.path, "rb")

	def test_get_message_for_email_entity(self):
		raw = b"""\
From: Orange Sheep <orange.sheep@world>

I like grass.
"""

		with patch("builtins.open", mock_open(read_data=raw)) as mock_file:
			email = MagicMock()
			email.envelope.path.return_value = "email.eml"
			message = utils.get_message_for_email_entity(email)
			self.assertEqual(message['From'], 'Orange Sheep <orange.sheep@world>')
			mock_file.assert_called_with(email.envelope.path, "rb")

	def test_get_content_as_safe_html(self):
		message = EmailMessage()
		message.set_content("""\
<head>
	<script></script>
</head>
<h1>Hi there!</h1>
<p>Let's open a</p>
<object>bakery</object>
""", subtype="html")

		content = utils.get_content_as_safe_html(message)
		self.assertEqual(content, """\
<h1>Hi there!</h1>
<p>Let's open a</p>
bakery""")

		message = EmailMessage()
		message.set_content("""\
It's a beautiful day,
it's a beautiful morning.
""", subtype="plain")
		content = utils.get_content_as_safe_html(message)
		self.assertEqual(content, "It&#39;s a beautiful day,<br />it&#39;s a beautiful morning.<br />")

		message = EmailMessage()
		message.set_content(b"{}", maintype="application", subtype="json")
		with self.assertRaises(Exception):
			utils.get_content_as_safe_html(message)

	def test_get_words_as_unsafe_text(self):
		message = EmailMessage()
		message.set_content("""\
<head>
	<script></script>
</head>
<h1>Hi there!</h1>
<p>Let's open a</p>
<object>bakery</object>
""", subtype="html")

		content = utils.get_words_as_unsafe_text(message)
		self.assertEqual(content, "Hi there! Let's open a bakery")

	def test_get_attachment_info(self):
		message = EmailMessage()
		message.add_attachment(b"Lorem Ipsum", maintype="text", subtype="plain", filename="lorem.txt")
		message.add_attachment(b"<Lorem />", maintype="text", subtype="xml", filename="lorem.xml")

		info = utils.get_attachment_info(message)
		self.assertEqual(info, [
			{'filename': 'lorem.txt', 'content_type': 'text/plain'},
			{'filename': 'lorem.xml', 'content_type': 'text/xml'},
		])

	def test_get_attachment(self):
		message = EmailMessage()
		message.add_attachment(b"Lorem Ipsum", maintype="text", subtype="plain", filename="lorem.txt")

		attachment = utils.get_attachment(message, 0)
		self.assertEqual(attachment, (b"Lorem Ipsum", "text/plain", "lorem.txt"))


class EmailViewTests(WebTest):
	@classmethod
	def setUpTestData(cls):
		message = EmailMessage()
		message.set_content("""\
Hello fellow sheep!

This morning, I found the location of some really tasty grass I want to share with you.

Mäh
Orange Sheep
""", subtype="plain")
		message.add_attachment(b"<Picture of tasty grass>", maintype="image", subtype="png", filename="grass.png")

		cls.sample_message = message

	@freeze_time("2013-03-07")
	def test_index_with_no_emails(self):
		response = self.app.get(reverse('emails:index'))
		self.assertRedirects(response, '/emails/2013/3')

	@freeze_time("2013-03-07")
	def test_index_with_emails(self):
		mommy.make(
			Email,
			date=make_aware(datetime(2012, 2, 6))
		)
		mommy.make(
			Email,
			date=make_aware(datetime(2014, 4, 8))
		)
		response = self.app.get(reverse('emails:index'))
		self.assertRedirects(response, '/emails/2014/4')

	def test_emails_archive_with_no_mails(self):
		response = self.app.get(reverse('emails:archive', args=(2013, 3)))
		self.assertContains(response, 'No emails found')

	def test_emails_archive(self):
		mommy.make(
			Email,
			subject='Test email A',
			date=make_aware(datetime(2013, 3, 7)),
			tree_id=1, lft=None, rght=None
		)
		mommy.make(
			Email,
			subject='Test email B',
			date=make_aware(datetime(2013, 3, 8)),
			tree_id=2, lft=None, rght=None
		)
		mommy.make(
			Email,
			subject='Test email C',
			date=make_aware(datetime(2013, 4, 7)),
			tree_id=3, lft=None, rght=None
		)
		response = self.app.get(reverse('emails:archive', args=(2013, 3)))
		html: BeautifulSoup = response.html
		self.assertContains(response, 'Test email A')
		self.assertContains(response, 'Test email B')
		self.assertNotContains(response, 'Test email C')

		self.assertHasText(html, "li", 'March 2013: 2')
		self.assertHasText(html, "li", 'April 2013: 1')

		self.assertHasLink(html, '/emails/2013/2', '← February 2013')
		self.assertHasLink(html, '/emails/2013/4', 'April 2013 →')

	def test_emails_view(self):
		storage = FileSystemStorage(tempfile.gettempdir())
		with patch("_1327.emails.models.Email.envelope.field.storage", new=storage):
			mommy.make(
				Email,
				id=1,
				date=make_aware(datetime(2013, 3, 7, 13, 37)),
				subject='I found some tasty grass!',
				text='unused text',
				from_name='Orange Sheep',
				from_address='orange@sheep',
				to_names=['Blue Sheep', 'Yellow Sheep'],
				to_addresses=['blue@sheep', 'yellow@sheep'],
				cc_names=['Green Sheep'],
				cc_addresses=['green@sheep'],
				envelope=ContentFile(self.sample_message.as_bytes(), name="email.eml"),
				_save_kwargs={'force_insert': True}
			)

			response = self.app.get(reverse('emails:view', args=(1,)))
			self.assertNotContains(response, "unused text")
			self.assertContains(response, "I found some tasty grass!")
			self.assertContains(response, "Orange Sheep")
			self.assertContains(response, "Blue Sheep")
			self.assertContains(response, "Yellow Sheep")
			self.assertContains(response, "Green Sheep")
			self.assertContains(response, "07.03.2013, 13:37")
			self.assertContains(response, "Hello fellow sheep!")
			self.assertContains(response, "grass.png")

	def test_emails_download(self):
		storage = FileSystemStorage(tempfile.gettempdir())
		with patch("_1327.emails.models.Email.envelope.field.storage", new=storage):
			message_as_bytes = self.sample_message.as_bytes()
			mommy.make(
				Email,
				id=1,
				envelope=ContentFile(message_as_bytes, name="email.eml"),
				_save_kwargs={'force_insert': True}
			)

			response = self.app.get(reverse('emails:download', args=(1,)))
			self.assertEqual(response['Content-Type'], 'message/rfc822')
			self.assertEqual(response.content, message_as_bytes)

	def test_emails_download_attachment(self):
		storage = FileSystemStorage(tempfile.gettempdir())
		with patch("_1327.emails.models.Email.envelope.field.storage", new=storage):
			mommy.make(
				Email,
				id=1,
				envelope=ContentFile(self.sample_message.as_bytes(), name="email.eml"),
				_save_kwargs={'force_insert': True}
			)

			response = self.app.get(reverse('emails:download_attachment', args=(1, 0)))
			self.assertEqual(response['Content-Type'], 'image/png')
			self.assertTrue('grass.png' in response['Content-Disposition'])
			attachments = list(self.sample_message.iter_attachments())
			self.assertEqual(response.content, attachments[0].get_content())

	def assertHasLink(self, html: BeautifulSoup, href: str, text: str):
		links = filter(lambda link: link.text.strip() == text, html.find_all("a", href=href))
		self.assertTrue(len(list(links)) > 0, msg=f'Could not find link with href "{href}" and text "{text}".')

	def assertHasText(self, html: BeautifulSoup, name: str, text: str):
		elements = filter(lambda element: element.text.strip() == text, html.find_all(name))
		self.assertTrue(len(list(elements)) > 0, msg=f'Could not find element "{name}" with text "{text}".')


class EmailViewSearchTests(WebTest):
	@classmethod
	def setUpTestData(cls):
		cls.SUBJECT1 = 'I like oranges'
		cls.SUBJECT2 = 'I like blue fruit'

		mommy.make(
			Email,
			from_name='Mr. Orange',
			from_address='orange@sheep',
			to_names=['Ms. Yellow'],
			to_addresses=['yellow@sheep'],
			subject=cls.SUBJECT1,
			text='and peaches!',
			num_attachments=2,
			date=make_aware(datetime(2013, 3, 6)),
		)
		mommy.make(
			Email,
			from_name='Ms. Blue',
			from_address='blue@sheep',
			cc_names=['Ms. Green'],
			cc_addresses=['green@sheep'],
			subject=cls.SUBJECT2,
			text="Sadly there isn't any :(",
			num_attachments=0,
			date=make_aware(datetime(2013, 3, 8)),
		)

	def test_emails_search_empty_query(self):
		response = self.app.get(reverse('emails:search'))
		self.assertContains(response, 'No emails found for the given search query.')

	def test_emails_search_subject(self):
		response = self.app.get(reverse('emails:search'), params={'text': 'oranges'})
		self.assertContains(response, self.SUBJECT1)
		self.assertNotContains(response, self.SUBJECT2)

	def test_emails_search_body(self):
		response = self.app.get(reverse('emails:search'), params={'text': ':('})
		self.assertNotContains(response, self.SUBJECT1)
		self.assertContains(response, self.SUBJECT2)

	def test_emails_search_from_name(self):
		response = self.app.get(reverse('emails:search'), params={'sender': 'Mr.'})
		self.assertContains(response, self.SUBJECT1)
		self.assertNotContains(response, self.SUBJECT2)

	def test_emails_search_from_address(self):
		response = self.app.get(reverse('emails:search'), params={'sender': 'blue'})
		self.assertNotContains(response, self.SUBJECT1)
		self.assertContains(response, self.SUBJECT2)

	def test_emails_search_to_name(self):
		response = self.app.get(reverse('emails:search'), params={'receiver': 'yellow'})
		self.assertContains(response, self.SUBJECT1)
		self.assertNotContains(response, self.SUBJECT2)

	def test_emails_search_to_address(self):
		response = self.app.get(reverse('emails:search'), params={'receiver': 'YELLOW@'})
		self.assertContains(response, self.SUBJECT1)
		self.assertNotContains(response, self.SUBJECT2)

	def test_emails_search_cc_name(self):
		response = self.app.get(reverse('emails:search'), params={'receiver': 'green'})
		self.assertNotContains(response, self.SUBJECT1)
		self.assertContains(response, self.SUBJECT2)

	def test_emails_search_cc_address(self):
		response = self.app.get(reverse('emails:search'), params={'receiver': 'GREEN@'})
		self.assertNotContains(response, self.SUBJECT1)
		self.assertContains(response, self.SUBJECT2)

	def test_emails_search_received_after(self):
		response = self.app.get(reverse('emails:search'), params={'received_after': '2013-03-07'})
		self.assertNotContains(response, self.SUBJECT1)
		self.assertContains(response, self.SUBJECT2)

	def test_emails_search_received_before(self):
		response = self.app.get(reverse('emails:search'), params={'received_before': '2013-03-07'})
		self.assertContains(response, self.SUBJECT1)
		self.assertNotContains(response, self.SUBJECT2)

	def test_emails_search_attachments(self):
		response = self.app.get(reverse('emails:search'), params={'has_attachments': 'yes'})
		self.assertContains(response, self.SUBJECT1)
		self.assertNotContains(response, self.SUBJECT2)
