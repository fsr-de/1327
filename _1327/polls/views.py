import datetime

import markdown
from django.contrib import messages
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.forms import formset_factory, inlineformset_factory
from django.http import Http404, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _
from markdown.extensions.toc import TocExtension

from _1327.documents.forms import get_permission_form
from _1327.documents.markdown_internal_link_extension import InternalLinksMarkdownExtension
from _1327.polls.forms import ChoiceForm, PollForm
from _1327.polls.models import Choice, Poll
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


def results(request, url_title):
	poll = get_object_or_error(Poll, request.user, ['polls.view_poll'], url_title=url_title)

	if poll.start_date > datetime.date.today():
		# poll is not open
		raise Http404

	if request.user.has_perm(Poll.VOTE_PERMISSION_NAME, poll) and not poll.participants.filter(id=request.user.pk).exists() and poll.end_date > datetime.date.today():
		messages.info(request, _("You have to vote before you can see the results!"))
		return vote(request, url_title)

	md = markdown.Markdown(safe_mode='escape', extensions=[TocExtension(baselevel=2), InternalLinksMarkdownExtension()])
	description = md.convert(poll.text)

	return render(
		request,
		'polls_results.html',
		{
			"document": poll,
			"description": description,
			'attachments': poll.attachments.filter(no_direct_download=False).order_by('index'),
		}
	)


def vote(request, url_title):
	poll = get_object_or_error(Poll, request.user, ['polls.view_poll', 'polls.vote_poll'], url_title=url_title)

	if poll.start_date > datetime.date.today():
		# poll is not open
		raise Http404

	if poll.end_date < datetime.date.today() or poll.participants.filter(id=request.user.pk).exists():
		messages.warning(request, _("You can not vote for polls that are already finished, or that you have already voted for!"))
		return results(request, url_title)

	if request.method == 'POST':
		choices = request.POST.getlist('choice')
		if len(choices) == 0:
			messages.error(request, _("You must select one Choice at least!"))
			return HttpResponseRedirect(reverse('documents:view', args=[url_title]))
		if len(choices) > poll.max_allowed_number_of_answers:
			messages.error(request, _("You can only select up to {} options!").format(poll.max_allowed_number_of_answers))
			return HttpResponseRedirect(reverse('documents:view', args=[url_title]))

		for choice_id in choices:
			choice = poll.choices.get(id=choice_id)
			choice.votes += 1
			choice.save()

		poll.participants.add(request.user)
		messages.success(request, _("We've received your vote!"))
		return results(request, url_title)

	md = markdown.Markdown(safe_mode='escape', extensions=[TocExtension(baselevel=2), InternalLinksMarkdownExtension()])
	description = md.convert(poll.text)

	return render(
		request,
		'polls_vote.html',
		{
			"document": poll,
			"description": description,
			"widget": "checkbox" if poll.max_allowed_number_of_answers != 1 else "radio"
		}
	)


def view(request, title):
	poll = Poll.objects.get(url_title=title)
	if poll.end_date < datetime.date.today() or poll.participants.filter(id=request.user.pk).exists():
		return results(request, title)
	else:
		return vote(request, title)
