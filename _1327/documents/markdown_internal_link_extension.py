import markdown

from _1327.documents.models import Document
from _1327.polls.models import Poll


class InternalLinksMarkdownExtension(markdown.extensions.Extension):

	def extendMarkdown(self, md):
		md.inlinePatterns.register(Document.LinkPattern(Document.DOCUMENT_LINK_REGEX, md), 'InternalLinkDocumentsPattern', 200)
		md.inlinePatterns.register(Poll.LinkPattern(Poll.POLLS_LINK_REGEX, md), 'InternalLinkPollsPattern', 200)
