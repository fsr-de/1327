from email import message_from_bytes, policy, utils
import poplib
import re
import sys
from typing import List

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management import BaseCommand

from _1327.emails.models import Email
from _1327.emails.utils import email_from_bytes, get_attachment_info, get_words_as_unsafe_text


class Command(BaseCommand):
	help = 'Imports new emails from a POP3 email account and deletes them from the server.'

	conn: poplib.POP3 = None

	def add_arguments(self, parser):
		parser.add_argument('--delete', action='store_true', help='Delete emails from server')

	def handle(self, *args, **options):
		if len(settings.EMAILS_POP3_HOST) == 0 or len(settings.EMAILS_POP3_USER) == 0 or len(settings.EMAILS_POP3_PASS) == 0:
			self.stdout.write("Please specify EMAILS_POP3_HOST, EMAILS_POP3_USER and EMAILS_POP3_PASS in your settings.")
			sys.exit(1)

		if settings.EMAILS_POP3_USE_SSL:
			self.conn = poplib.POP3_SSL(settings.EMAILS_POP3_HOST, port=settings.EMAILS_POP3_PORT)
		else:
			self.conn = poplib.POP3(settings.EMAILS_POP3_HOST, port=settings.EMAILS_POP3_PORT)

		self.conn.user(settings.EMAILS_POP3_USER)
		self.conn.pass_(settings.EMAILS_POP3_PASS)

		total_messages = self.get_num_messages()
		print(f"{total_messages} messages in total.")

		message_numbers = self.get_message_numbers()
		non_spam_numbers, spam_numbers = self.partition_by_spam(message_numbers)
		print(f"{len(non_spam_numbers)} non-spam emails, {len(spam_numbers)} spam emails.")

		non_spam_messages = [self.retrieve_message(num) for num in non_spam_numbers]
		print("Non-spam emails retrieved.")

		for num in message_numbers:
			self.verify_response_ok(self.conn.dele(num))
		print("All emails marked for deletion.")

		for raw_message in non_spam_messages:
			message = email_from_bytes(raw_message)

			sender = utils.parseaddr(message.get('From', []))
			to = list(zip(*utils.getaddresses(message.get_all('To', []))))
			if len(to) == 0:
				to = [[], []]
			cc = list(zip(*utils.getaddresses(message.get_all('CC', []))))
			if len(cc) == 0:
				cc = [[], []]

			references = message.get('References')
			if references is not None:
				references = [utils.unquote(ref.strip()) for ref in re.split("[ ,]", references)]
			else:
				references = []

			email = Email(
				from_name=sender[0],
				from_address=sender[1],
				to_names=to[0],
				to_addresses=to[1],
				cc_names=cc[0],
				cc_addresses=cc[1],
				subject=message.get('subject', '').strip(),
				text=get_words_as_unsafe_text(message),
				date=utils.parsedate_to_datetime(message.get('Date')),
				message_id=utils.unquote(message.get('Message-Id')),
				in_reply_to=utils.unquote(message.get('In-Reply-To', '')),
				references=references,
				num_attachments=len(get_attachment_info(message))
			)

			email.save()
			email.envelope.save(str(email.id) + ".eml", ContentFile(raw_message))

			self.verify_response_ok(self.conn.noop())

		# Now create the parent-child relationship.
		# We can't do it while inserting the emails in the for-loop above, because the emails may be retrieved
		# in any order. As such, the parent might not have been inserted when the child is inserted.
		emails_with_reply_to_but_no_parent = Email.objects.filter(in_reply_to__isnull=False, parent__isnull=True)
		for email in emails_with_reply_to_but_no_parent:
			possible_parents = Email.objects.filter(message_id=email.in_reply_to)
			if len(possible_parents) >= 1:
				parent = possible_parents[0]
				if len(possible_parents) >= 2:
					print("Ambiguous In-Reply-To header")
				email.parent = parent
				email.save()

			self.verify_response_ok(self.conn.noop())

		self.verify_response_ok(self.conn.quit())
		print("Connection closed and emails deleted from server.")

	def is_spam(self, message_number: str):
		response = self.conn.top(message_number, 0)
		self.verify_response_ok(response)
		message = message_from_bytes(self.message_bytes_from_response(response), policy=policy.default)
		return message.get('X-Spam-Flag', '').upper().startswith('YES') or message.get('X-Spam-Flag2', '').upper().startswith('YES')

	def retrieve_message(self, message_number: str) -> bytes:
		response = self.conn.retr(message_number)
		self.verify_response_ok(response)
		return self.message_bytes_from_response(response)

	def get_message_numbers(self) -> List[str]:
		response = self.conn.list()
		self.verify_response_ok(response)
		# Each entry contains a string with the message number, a space, and the message size.
		nums = response[1]
		return [num.decode("ASCII").split(" ", 1)[0] for num in nums]

	def get_num_messages(self):
		stat = self.conn.stat()
		total_messages = stat[0]
		return total_messages

	def verify_response_ok(self, response):
		status = response[0] if isinstance(response, tuple) else response
		if not status.startswith(b'+OK'):
			raise Exception(f"Expected response to start with +OK, but got {status}")

	def message_bytes_from_response(self, response):
		return b'\r\n'.join(response[1])

	def partition_by_spam(self, message_numbers):
		spam_numbers = []
		non_spam_numbers = []
		for num in message_numbers:
			if self.is_spam(num):
				spam_numbers.append(num)
			else:
				non_spam_numbers.append(num)
		return non_spam_numbers, spam_numbers
