from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _

import markdown
from markdown.inlinepatterns import LinkPattern


class InternalLinkPattern(LinkPattern):

	def handleMatch(self, m):
		el = markdown.util.etree.Element("a")
		try:
			el.set('href', self.url(m.group('id')))
			el.text = markdown.util.AtomicString(m.group('title'))
		except ObjectDoesNotExist:
			el.text = markdown.util.AtomicString(_('[missing link]'))
		return el

	def url(id):
		raise NotImplementedError
