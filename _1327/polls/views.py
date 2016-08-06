import datetime


from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db.models import F
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _

import markdown
from markdown.extensions.toc import TocExtension

from _1327.documents.markdown_internal_link_extension import InternalLinksMarkdownExtension
from _1327.polls.models import Poll
from _1327.user_management.shortcuts import get_object_or_error


def list(request):
	running_polls = []
	finished_polls = []
	upcoming_polls = []
	# do not show polls that a user is not allowed to see
	for poll in Poll.objects.all():
		if request.user.has_perm(Poll.VIEW_PERMISSION_NAME, obj=poll) and poll.start_date <= datetime.date.today():
			if datetime.date.today() <= poll.end_date \
						and not poll.participants.filter(id=request.user.pk).exists() \
						and request.user.has_perm(Poll.VOTE_PERMISSION_NAME, poll):
				running_polls.append(poll)
			else:
				finished_polls.append(poll)
		elif request.user.has_perm("polls.change_poll", obj=poll) and poll.start_date > datetime.date.today():
			upcoming_polls.append(poll)

	return render(
		request,
		'polls_index.html',
		{
			"running_polls": running_polls,
			"finished_polls": finished_polls,
			"upcoming_polls": upcoming_polls,
		}
	)


def results(request, poll, url_title):
	if poll.start_date > datetime.date.today():
		# poll is not open
		raise Http404

	if request.user.has_perm(Poll.VOTE_PERMISSION_NAME, poll) \
				and not poll.participants.filter(id=request.user.pk).exists() \
				and poll.end_date > datetime.date.today():
		return vote(request, poll, url_title)

	md = markdown.Markdown(safe_mode='escape', extensions=[TocExtension(baselevel=2), InternalLinksMarkdownExtension()])
	description = md.convert(poll.text)

	return render(
		request,
		'polls_results.html',
		{
			"document": poll,
			"description": description,
			'toc': md.toc,
			'active_page': 'view',
			'attachments': poll.attachments.filter(no_direct_download=False).order_by('index'),
		}
	)


def vote(request, poll, url_title):
	if poll.start_date > datetime.date.today():
		# poll is not open
		raise Http404

	if poll.end_date < datetime.date.today() or poll.participants.filter(id=request.user.pk).exists():
		return results(request, poll, url_title)

	if request.method == 'POST':
		choices = request.POST.getlist('choice')
		if len(choices) == 0:
			messages.error(request, _("You must select one Choice at least!"))
			return HttpResponseRedirect(reverse('documents:view', args=[url_title]))
		if len(choices) > poll.max_allowed_number_of_answers:
			messages.error(request, _("You can only select up to {} options!").format(poll.max_allowed_number_of_answers))
			return HttpResponseRedirect(reverse('documents:view', args=[url_title]))

		for choice_id in choices:
			choice = poll.choices.filter(id=choice_id)
			choice.update(votes=F('votes') + 1)

		poll.participants.add(request.user)
		messages.success(request, _("We've received your vote!"))
		return HttpResponseRedirect(reverse('documents:view', args=[url_title]))

	md = markdown.Markdown(safe_mode='escape', extensions=[TocExtension(baselevel=2), InternalLinksMarkdownExtension()])
	description = md.convert(poll.text)

	return render(
		request,
		'polls_vote.html',
		{
			"document": poll,
			"description": description,
			'toc': md.toc,
			'active_page': 'view',
			"widget": "checkbox" if poll.max_allowed_number_of_answers != 1 else "radio",
			'attachments': poll.attachments.filter(no_direct_download=False).order_by('index'),
		}
	)


def view(request, title):
	poll = get_object_or_error(Poll, request.user, ['polls.view_poll'], url_title=title)
	if poll.end_date < datetime.date.today() or poll.participants.filter(id=request.user.pk).exists():
		return results(request, poll, title)
	else:
		if not request.user.has_perm('polls.vote_poll', poll):
			return results(request, poll, title)
		return vote(request, poll, title)
