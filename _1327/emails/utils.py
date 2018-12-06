import email
from email import policy
from typing import Dict, List, Tuple

import bleach
from django.utils.html import escape
from django.utils.safestring import mark_safe


def get_raw_email_for_email_entity(email_entity):
	with open(email_entity.envelope.path, "rb") as envelope:
		return envelope.read()


def get_message_for_email_entity(email_entity) -> email.message.Message:
	return email.message_from_bytes(get_raw_email_for_email_entity(email_entity), policy=policy.default)


def get_content_as_safe_html(message) -> str:
	content, content_type = find_content(message)
	return content_to_safe_string(content, content_type)


def get_content_as_unsafe_text(message):
	content, content_type = find_content(message)

	# TODO: Only strip HTML tags, don't convert stuff to HTML entities
	return bleach.clean(content, tags=[], attributes={}, styles=[], strip=True).strip()


def find_content(message: email.message.MIMEPart) -> Tuple[str, str]:
	body = message.get_body(('html', 'plain'))
	content_type = body.get_content_type()
	content = body.get_content()

	return content, content_type


def get_attachment(message: email.message.MIMEPart, index: int) -> Tuple[bytes, str, str]:
	parts = get_attachment_parts(message)
	assert(index < len(parts))
	part = parts[index]
	filename = get_attachment_info(message)[index]['filename']
	return part.get_payload(decode=True), part.get_content_type(), filename


def get_attachment_info(message: email.message.MIMEPart) -> List[Dict]:
	attachments = []
	for part in get_attachment_parts(message):
		content_type = part.get_content_type()
		filename = part.get_filename("unknown name")
		if content_type == 'message/rfc822':
			attachment_message = part.get_payload()[0] if part.is_multipart() else part.get_payload()
			filename = f"{attachment_message.get('Subject', 'unknown name')}.eml"
		attachments.append({'filename': filename, 'content_type': content_type})

	return attachments


def get_attachment_parts(message: email.message.EmailMessage) -> List[email.message.Message]:
	return [part for part in message.walk() if part.is_attachment() or part.get_content_type() == 'message/rfc822']


def content_to_safe_string(content, content_type) -> str:
	if content_type == 'text/plain':
		content = mark_safe(escape(content).replace('\n', '<br />'))
	elif content_type == 'text/html':
		allowed_tags = bleach.sanitizer.ALLOWED_TAGS
		allowed_tags.extend(['p', 'br', 'div'])
		content = mark_safe(bleach.clean(content, tags=allowed_tags, strip=True))
	else:
		raise Exception('Invalid content type: {}'.format(content_type))
	return content
