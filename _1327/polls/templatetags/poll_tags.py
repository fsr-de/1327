import datetime

from django import template

from _1327.polls.models import Poll

register = template.Library()


@register.filter
def can_see_results(poll):
	if poll.state == Poll.UNPUBLISHED:
		return False
	elif poll.state == Poll.AFTER_END:
		if poll.end_date >= datetime.date.today():
			return False
		else:
			return True
	elif poll.state == Poll.PUBLISHED:
		return True
	else:
		return False  # TODO: raise Exception?


@register.filter
def one_day_later(date):
	return date + datetime.timedelta(days=1)
