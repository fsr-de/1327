from email import utils
from email.message import EmailMessage
from hashlib import md5
from io import BytesIO
import json
from random import randrange

from faker import Faker
from twisted.cred.checkers import InMemoryUsernamePasswordDatabaseDontUse
from twisted.cred.portal import IRealm, Portal
from twisted.internet import reactor
from twisted.internet.protocol import ServerFactory
from twisted.mail import pop3
from twisted.mail.pop3 import IMailbox
from zope.interface import implementer


# Based on the example provided by Pepijn de Vos
# at http://pepijndevos.nl/twisted-pop3-example-server/index.html
def get_reactor(messages):
	@implementer(IMailbox)
	class SimpleMailbox:
		def __init__(self):
			self.messages = messages
			self.marked_for_deletion = []

		def listMessages(self, index=None):
			if index is not None:
				if index in self.marked_for_deletion or index >= len(self.messages):
					raise ValueError()
				return len(self.messages[index].as_bytes())
			else:
				return [len(m.as_bytes()) for idx, m in enumerate(self.messages) if idx not in self.marked_for_deletion]

		def getMessage(self, index):
			if index in self.marked_for_deletion or index >= len(self.messages):
				raise ValueError()
			return BytesIO(self.messages[index].as_bytes())

		def getUidl(self, index):
			if index in self.marked_for_deletion or index >= len(self.messages):
				raise ValueError()
			return md5(self.messages[index].as_bytes()).hexdigest()

		def deleteMessage(self, index):
			if index in self.marked_for_deletion or index >= len(self.messages):
				raise ValueError()
			self.marked_for_deletion.append(index)

		def undeleteMessages(self):
			self.marked_for_deletion = []

		def sync(self):
			self.messages = [m for idx, m in enumerate(self.messages) if idx not in self.marked_for_deletion]
			self.marked_for_deletion = []

	@implementer(IRealm)
	class SimpleRealm:
		def requestAvatar(self, avatarId, mind, *interfaces):
			if IMailbox in interfaces:
				return IMailbox, mailbox, lambda: None
			else:
				raise NotImplementedError()

	mailbox = SimpleMailbox()
	portal = Portal(SimpleRealm())

	checker = InMemoryUsernamePasswordDatabaseDontUse()
	checker.addUser(b"1327", b"1327")
	portal.registerChecker(checker)

	f = ServerFactory()
	f.protocol = pop3.POP3
	f.protocol.portal = portal

	reactor.listenTCP(1327, f)

	return reactor, mailbox


if __name__ == "__main__":
	fake = Faker()
	messages = []
	for i in range(400):
		message = EmailMessage()
		message['From'] = utils.formataddr((fake.name(), fake.email()))
		message['To'] = utils.formataddr((fake.name(), fake.email()))
		if fake.boolean(20):
			num_cc = randrange(1, 5)
			cc = []
			for j in range(num_cc):
				cc.append(utils.formataddr((fake.name(), fake.email())))
			message['CC'] = ", ".join(cc)
		message['Subject'] = fake.sentence(nb_words=8, variable_nb_words=True)
		message['Date'] = fake.date_time_between(start_date="-8w", end_date="now")
		message.set_content(fake.text(max_nb_chars=600), subtype="plain")
		message['Message-ID'] = f"<message-{i}@messages>"
		if fake.boolean(10):
			message['X-Spam-Flag' if fake.boolean() else 'X-Spam-Flag2'] = "YES"

		if fake.boolean(20):
			content = json.dumps(fake.pydict(10, True, str, int)).encode("utf-8")
			message.add_attachment(content, maintype="application", subtype="json", filename=fake.file_name(extension='json'))

		if fake.boolean(30) and i > 0:
			parent_num = randrange(0, i)
			if parent_num != i:
				message['In-Reply-To'] = f"<message-{parent_num}@messages>"

		messages.append(message)

	app, mailbox = get_reactor(messages)
	app.run()
