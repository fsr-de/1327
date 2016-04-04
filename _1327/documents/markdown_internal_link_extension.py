import markdown

from _1327.documents.models import Document
from _1327.polls.models import Poll


class InternalLinksMarkdownExtension(markdown.extensions.Extension):

	def extendMarkdown(self, md, md_globals):
		md.inlinePatterns.add('InternalLinkDocumentsPattern', Document.LinkPattern(Document.DOCUMENT_LINK_REGEX, md), "_begin")
		md.inlinePatterns.add('InternalLinkPollsPattern', Poll.LinkPattern(Poll.POLLS_LINK_REGEX, md), "_begin")
