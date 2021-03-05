from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _

import markdown
from markdown.inlinepatterns import LinkInlineProcessor


class InternalLinkPattern(LinkInlineProcessor):

	def handleMatch(self, m, data=None):
		el = markdown.util.etree.Element("a")
		try:
			el.set('href', self.url(m.group('id')))
			el.text = markdown.util.AtomicString(m.group('title'))
		except ObjectDoesNotExist:
			el.text = markdown.util.AtomicString(_('[missing link]'))
		return el, m.start(0), m.end(0)

	def url(id):
		raise NotImplementedError
