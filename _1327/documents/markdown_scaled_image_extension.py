from markdown import Extension
from markdown.inlinepatterns import BRK, dequote, handleAttributes, LinkPattern
from markdown.util import etree


# Mostly copied from default "ImagePattern"
SCALED_IMAGE_LINK_RE = r'\!' + BRK + r'\s*\(\s*(<.*?>|([^"\)\s]+\s*"[^"]*"|[^\)\s]*))\s+=(\d+)?x(\d+)?\s*\)'


class ScaledImageExtension(Extension):
	def extendMarkdown(self, md, md_globals):
		md.registerExtension(self)
		md.inlinePatterns['scaled_image_link'] = ScaledImagePattern(SCALED_IMAGE_LINK_RE, md)


class ScaledImagePattern(LinkPattern):
	def handleMatch(self, m):
		# Copied from default "ImagePattern"
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
		# End of copy

		width = m.group(11)
		if width:
			el.set('width', width + 'px')
		height = m.group(12)
		if height:
			el.set('height', height + 'px')

		# Copied from default "ImagePattern"
		if self.markdown.enable_attributes:
			truealt = handleAttributes(m.group(2), el)
		else:
			truealt = m.group(2)

		el.set('alt', self.unescape(truealt))
		return el
		# End of copy


def makeExtension():
	return ScaledImageExtension()
