import markdown
from markdown.inlinepatterns import LinkPattern


class InternalLinkPattern (LinkPattern):

	def handleMatch(self, m):
		el = markdown.util.etree.Element("a")
		el.set('href', self.url(m.group('id')))
		el.text = markdown.util.AtomicString(m.group('title'))
		return el

	def url(id):
		raise NotImplementedError
