import markdown

from _1327.information_pages.models import InformationDocument
from _1327.minutes.models import MinutesDocument
from _1327.polls.models import Poll


class InternalLinksMarkdownExtension(markdown.extensions.Extension):

	def extendMarkdown(self, md, md_globals):
		md.inlinePatterns.add('InternalLinkMinutesPattern', MinutesDocument.LinkPattern(MinutesDocument.MINUTES_LINK_REGEX, md), "_begin")
		md.inlinePatterns.add('InternalLinkPollsPattern', Poll.LinkPattern(Poll.POLLS_LINK_REGEX, md), "_begin")
		md.inlinePatterns.add('InternalLinkInformationDocumentPattern', InformationDocument.LinkPattern(InformationDocument.INFORMATIONDOCUMENT_LINK_REGEX, md), "_begin")
