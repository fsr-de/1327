from datetime import datetime
from email.message import EmailMessage
from unittest.mock import MagicMock, patch, mock_open

from django.test import TestCase

from _1327.emails import utils
from _1327.emails.forms import QuickSearchForm, SearchForm
from _1327.emails.models import Email


class FormTests(TestCase):
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


class ModelTest(TestCase):
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
		email = Email()
		with self.assertRaises(Exception):
			email.envelope.field.upload_to(email, "ignored-filename")

		email = Email(id=42, date=datetime(2018, 12, 12))
		path = email.envelope.field.upload_to(email, "ignored-filename")
		self.assertEqual(path, "emails/2018/12/42.eml")


class UtilsTest(TestCase):
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
