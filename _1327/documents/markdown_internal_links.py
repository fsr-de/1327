from django.core.urlresolvers import reverse
import markdown
from markdown.inlinepatterns import LinkPattern

from _1327.information_pages.models import InformationDocument
from _1327.minutes.models import MinutesDocument
from _1327.polls.models import Poll


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
			return reverse('minutes:view', args=[document.url_title])
		return ''


class InternalLinkPollsPattern (InternalLinkPattern):

	def url(self, id):
		poll = Poll.objects.get(id=id)
		if poll:
			return reverse('polls:results', args=[poll.id])
		return ''


class InternalLinkInformationDocumentPattern (InternalLinkPattern):

	def url(self, id):
		document = InformationDocument.objects.get(id=id)
		if document:
			return reverse('information_pages:view_information', args=[document.url_title])
		return ''


class InternalLinksMarkdownExtension(markdown.extensions.Extension):

	def extendMarkdown(self, md, md_globals):
		md.inlinePatterns.add('InternalLinkMinutesPattern', InternalLinkMinutesPattern(MinutesDocument.MINUTES_LINK_REGEX, md), "_begin")
		md.inlinePatterns.add('InternalLinkPollsPattern', InternalLinkPollsPattern(Poll.POLLS_LINK_REGEX, md), "_begin")
		md.inlinePatterns.add('InternalLinkInformationDocumentPattern', InternalLinkInformationDocumentPattern(InformationDocument.INFORMATIONDOCUMENT_LINK_REGEX, md), "_begin")
