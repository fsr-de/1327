from datetime import datetime
from email.message import EmailMessage
from email.utils import make_msgid
from hashlib import md5
from io import BytesIO
from random import random

from twisted.cred.checkers import InMemoryUsernamePasswordDatabaseDontUse
from twisted.cred.portal import IRealm, Portal
from twisted.internet import reactor
from twisted.internet.protocol import ServerFactory
from twisted.mail import pop3
from twisted.mail.pop3 import IMailbox
from zope.interface import implementer


# Based on the example provided by Pepijn de Vos
# at http://pepijndevos.nl/twisted-pop3-example-server/index.html
def get_reactor(n_non_spam, n_spam):

	@implementer(IMailbox)
	class SimpleMailbox:
		def __init__(self):
			self.messages = []

			for i in range(n_spam + n_non_spam):
				msg = EmailMessage()
				msg['Subject'] = f'Test Message {i + 1}'
				msg['From'] = 'Orange Sheep <orange@sheep>'
				msg['To'] = 'Yellow Sheep <yellow@sheep>'
				msg['CC'] = 'Blue Sheept <blue@sheep>'
				msg['Message-Id'] = make_msgid(domain='sheep')
				msg['Date'] = datetime.now()
				msg.set_content("""\
Hello fellow sheep!

This morning, I found the location of some really tasty grass I want to share with you.

Mäh
Orange Sheep
""")

				if i >= n_non_spam:
					if random() > 0.5:
						msg['X-Spam-Flag'] = "YES"
					else:
						msg['X-Spam-Flag2'] = "YES"

				self.messages.append(msg)

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
