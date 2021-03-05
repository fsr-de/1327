import datetime
import logging

from django.conf import settings
from django.core.mail import EmailMessage
from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy as _

from _1327.minutes.models import MinutesDocument

logger = logging.getLogger(__name__)


class Command(BaseCommand):
	args = ''
	help = 'Send reminders for unpublished minutes'

	def handle(self, *args, **options):
		check_date = datetime.date.today() - datetime.timedelta(days=settings.MINUTES_PUBLISH_REMINDER_DAYS)
		due_unpublished_minutes_documents = MinutesDocument.objects.filter(state=MinutesDocument.UNPUBLISHED, date=check_date)
		for minutes_document in due_unpublished_minutes_documents:
			if minutes_document.moderator and minutes_document.moderator.email:
				to_email = [minutes_document.moderator.email]
				cc_email = [minutes_document.author.email]
			else:
				to_email = [minutes_document.author.email]
				cc_email = []
			mail = EmailMessage(
				subject=_("Minutes publish reminder"),
				body=_('Please remember to publish the minutes document "{}" from {} ({}).'.format(
					minutes_document.title,
					minutes_document.date.strftime("%d.%m.%Y"),
					settings.PAGE_URL + minutes_document.get_view_url()
				)),
				to=to_email,
				cc=cc_email,
				bcc=[a[1] for a in settings.ADMINS]
			)
			try:
				mail.send(False)
			except Exception:
				logger.exception('An exception occurred when sending the following email to user "{}":\n{}\n'.format(minutes_document.author.username, mail.message()))
