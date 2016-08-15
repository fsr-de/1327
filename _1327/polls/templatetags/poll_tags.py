import datetime
from django import template

register = template.Library()


@register.filter
def can_see_results(poll):
	if not poll.show_results_immediately and poll.end_date >= datetime.date.today():
		return False
	else:
		return True


@register.filter
def one_day_later(date):
	return date + datetime.timedelta(days=1)
