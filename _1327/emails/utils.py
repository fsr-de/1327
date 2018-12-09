from email import message_from_bytes, policy
from html import unescape

import bleach
from django.utils.html import escape
from django.utils.safestring import mark_safe


def email_from_bytes(email_bytes):
	return message_from_bytes(email_bytes, policy=policy.default)


def get_raw_email_for_email_entity(email_entity):
	with open(email_entity.envelope.path, "rb") as envelope:
		return envelope.read()


def get_message_for_email_entity(email_entity):
	return email_from_bytes(get_raw_email_for_email_entity(email_entity))


def get_content_as_safe_html(message) -> str:
	content, content_type = _find_content(message)

	if content_type == 'text/plain':
		content = mark_safe(escape(content).replace('\n', '<br />'))
	elif content_type == 'text/html':
		allowed_tags = bleach.sanitizer.ALLOWED_TAGS
		allowed_tags.extend(['p', 'br', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
		content = mark_safe(bleach.clean(content, tags=allowed_tags, strip=True).strip())
	else:
		raise Exception('Invalid content type: {}'.format(content_type))
	return content


def get_words_as_unsafe_text(message):
	content, content_type = _find_content(message)

	# We first remove all HTML tags and encode all special characters (i.e. ">" -> "&gt;").
	# Then be unescape the decoded special characters. This results in a version with all
	# HTML tags stripped but the special characters not HTML encoded.
	content = unescape(bleach.clean(content, tags=[], attributes={}, styles=[], strip=True))

	# This replaces all occurrences of multiple whitespace characters by a single space.
	# Newline characters are replaced as well.
	return " ".join(content.split())


def get_attachment_info(message):
	attachments = []
	for part in _get_attachment_parts(message):
		content_type = part.get_content_type()
		filename = part.get_filename("unknown name")
		if content_type == 'message/rfc822':
			attachment_message = part.get_payload()[0] if part.is_multipart() else part.get_payload()
			filename = f"{attachment_message.get('Subject', 'unknown name')}.eml"
		attachments.append({'filename': filename, 'content_type': content_type})

	return attachments


def get_attachment(message, index):
	parts = _get_attachment_parts(message)
	part = parts[index]
	filename = get_attachment_info(message)[index]['filename']
	return part.get_payload(decode=True), part.get_content_type(), filename


def _find_content(message):
	body = message.get_body(('html', 'plain'))
	content_type = body.get_content_type()
	content = body.get_content()

	return content, content_type


def _get_attachment_parts(message):
	return [part for part in message.walk() if part.is_attachment() or part.get_content_type() == 'message/rfc822']
