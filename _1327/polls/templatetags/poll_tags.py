import datetime

from django import template

from _1327.polls.models import Poll

register = template.Library()


@register.filter
def can_see_results(poll):
	if poll.state == Poll.UNPUBLISHED:
		return False
	if poll.state == Poll.AFTER_END and poll.end_date >= datetime.date.today():
		return False
	else:
		return True
	if poll.state == Poll.PUBLISHED:
		return True


@register.filter
def one_day_later(date):
	return date + datetime.timedelta(days=1)
