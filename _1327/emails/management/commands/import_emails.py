import sys
from email import message_from_bytes, policy, utils
import poplib
import re
from typing import List

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management import BaseCommand

from _1327.emails.models import Email
from _1327.emails.utils import get_attachment_info, get_content_as_unsafe_text


class Command(BaseCommand):
	help = 'Imports new emails from a POP3 email account and deletes them from the server.'

	conn: poplib.POP3_SSL = None

	def handle(self, *args, **options):
		if len(settings.EMAILS_POP3_HOST) == 0 or len(settings.EMAILS_POP3_USER) == 0 or len(settings.EMAILS_POP3_PASS) == 0:
			self.stdout.write("Please specify EMAILS_POP3_HOST, EMAILS_POP3_USER and EMAILS_POP3_PASS in your settings.")
			sys.exit(1)

		self.conn = poplib.POP3_SSL(settings.EMAILS_POP3_HOST)
		self.conn.user(settings.EMAILS_POP3_USER)
		self.conn.pass_(settings.EMAILS_POP3_PASS)

		stat = self.conn.stat()
		total_messages = stat[0]
		print("{} messages in total.".format(total_messages))

		message_numbers = self.get_message_numbers()
		non_spam_numbers = [num for num in message_numbers if not self.is_spam(num)]
		non_spam_messages = [self.retrieve_message(num) for num in non_spam_numbers]

		self.conn.quit()

		for raw_message in non_spam_messages:
			message = message_from_bytes(raw_message, policy=policy.default)

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

			in_reply_to = utils.unquote(message.get('In-Reply-To', ''))

			text = get_content_as_unsafe_text(message)

			envelope = ContentFile(raw_message)

			email = Email(
				from_name=sender[0],
				from_address=sender[1],
				to_names=to[0],
				to_addresses=to[1],
				cc_names=cc[0],
				cc_addresses=cc[1],
				subject=message.get('subject', '').strip(),
				text=text,
				date=utils.parsedate_to_datetime(message.get('Date')),
				message_id=utils.unquote(message.get('Message-Id')),
				in_reply_to=in_reply_to,
				references=references,
				trello_card_id=None,
				archived=False,
				num_attachments=len(get_attachment_info(message))
			)

			email.save(force_insert=True)
			email.envelope.save(str(email.id) + ".eml", envelope)

		# Now create the parent-child relationship.
		# We can't do it while inserting the emails in the for-loop above, because the emails may be retrieved
		# in any order.
		emails_with_reply_to_but_no_parent = Email.objects.filter(in_reply_to__isnull=False, parent__isnull=True)
		for email in emails_with_reply_to_but_no_parent:
			possible_parents = Email.objects.filter(message_id=email.in_reply_to)
			if len(possible_parents) >= 1:
				parent = possible_parents[0]
				if len(possible_parents) >= 2:
					print("Ambiguous In-Reply-To header")
				email.parent = parent
				email.save()

		# TODO: Delete retrieved messages from server.

	def is_spam(self, message_number: str):
		response = self.conn.top(message_number, 0)
		assert(response[0] == b'+OK')
		raw_message = b'\r\n'.join(response[1])

		message = message_from_bytes(raw_message, policy=policy.default)
		return message.get('X-Spam-Flag', '').upper().startswith('YES') or message.get('X-Spam-Flag2', '').upper().startswith('YES')

	def retrieve_message(self, message_number: str) -> bytes:
		response = self.conn.retr(message_number)
		assert(response[0].startswith(b'+OK'))
		return b'\r\n'.join(response[1])

	def get_message_numbers(self) -> List[str]:
		response = self.conn.list()
		assert(response[0].startswith(b'+OK'))
		nums = response[1]
		return [num.decode("Latin1").split(" ", 1)[0] for num in nums]
