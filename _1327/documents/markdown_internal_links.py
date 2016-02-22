import markdown
from markdown.inlinepatterns import LinkPattern

from _1327.information_pages.models import InformationDocument
from _1327.minutes.models import MinutesDocument
from _1327.polls.models import Poll

MINUTES_RE = r'\[(?P<title>[^\[]+)\]\(minutes:(?P<id>\d+)\)'
POLLS_RE = r'\[(?P<title>[^\[]+)\]\(poll:(?P<id>\d+)\)'
INFORMATION_DOCUMENT_RE = r'\[(?P<title>[^\[]+)\]\(information_document:(?P<id>\d+)\)'


class InternalLinkPattern (LinkPattern):

	def handleMatch(self, m):
		el = markdown.util.etree.Element("a")
		el.set('href', self.url(m.group('id')))
		el.text = markdown.util.AtomicString(m.group('title'))
		return el

	def url(id):
		raise NotImplementedError


class InternalLinkMinutesPattern (InternalLinkPattern):

	def url(self, id):
		document = MinutesDocument.objects.get(id=id)
		if document:
			return '/minutes/' + document.url_title
		return ''


class InternalLinkPollsPattern (InternalLinkPattern):

	def url(self, id):
		poll = Poll.objects.get(id=id)
		if poll:
			return '/polls/' + str(poll.id) + '/results'
		return ''


class InternalLinkInformationDocumentPattern (InternalLinkPattern):

	def url(self, id):
		document = InformationDocument.objects.get(id=id)
		if document:
			return '/' + document.url_title
		return ''


class InternalLinksMarkdownExtension(markdown.extensions.Extension):

	def extendMarkdown(self, md, md_globals):
		md.inlinePatterns.add('InternalLinkMinutesPattern', InternalLinkMinutesPattern(MINUTES_RE, md), "_begin")
		md.inlinePatterns.add('InternalLinkPollsPattern', InternalLinkPollsPattern(POLLS_RE, md), "_begin")
		md.inlinePatterns.add('InternalLinkInformationDocumentPattern', InternalLinkInformationDocumentPattern(INFORMATION_DOCUMENT_RE, md), "_begin")
