from markdown import Extension
from markdown.inlinepatterns import dequote, Pattern
from markdown.util import etree


NOBRACKET = r'[^\]\[]*'
BRK = (
	r'\[('
	+ (NOBRACKET + r'(\[') * 6
	+ (NOBRACKET + r'\])*') * 6
	+ NOBRACKET + r')\]'
)
SCALED_IMAGE_LINK_RE = r'\!' + BRK + r'\s*\(\s*(<.*?>|([^"\)\s]+\s*"[^"]*"|[^\)\s]*))\s+=(\d+)?x(\d+)?\s*\)'


class ScaledImageExtension(Extension):
	def extendMarkdown(self, md):
		md.registerExtension(self)
		md.inlinePatterns.register(ScaledImagePattern(SCALED_IMAGE_LINK_RE, md), 'scaled_image_link', 200)


class ScaledImagePattern(Pattern):
	def handleMatch(self, m, data=None):
		# Mostly copied from (deprecated) default "ImagePattern"
		el = etree.Element("img")
		src_parts = m.group(9).split()
		if src_parts:
			src = src_parts[0]
			if src[0] == "<" and src[-1] == ">":
				src = src[1:-1]
			el.set('src', self.unescape(src))
		else:
			el.set('src', "")
		if len(src_parts) > 1:
			el.set('title', dequote(self.unescape(" ".join(src_parts[1:]))))

		width = m.group(11)
		if width:
			el.set('width', width + 'px')
		height = m.group(12)
		if height:
			el.set('height', height + 'px')

		el.set('alt', self.unescape(m.group(2)))
		return el


def makeExtension():
	return ScaledImageExtension()
