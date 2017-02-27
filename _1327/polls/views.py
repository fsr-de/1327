import datetime


from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db.models import F
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.utils.translation import ugettext_lazy as _

import markdown
from markdown.extensions.toc import TocExtension

from _1327.documents.markdown_internal_link_extension import InternalLinksMarkdownExtension
from _1327.documents.models import Document
from _1327.main.utils import abbreviation_explanation_markdown, document_permission_overview
from _1327.polls.models import Poll
from _1327.user_management.shortcuts import check_permissions


def index(request):
	running_polls = []
	finished_polls = []
	upcoming_polls = []
	# do not show polls that a user is not allowed to see
	for poll in Poll.objects.all().order_by('-end_date'):
		if request.user.has_perm(Poll.get_view_permission(), obj=poll) and poll.start_date <= datetime.date.today():
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

	if request.user.has_perm(Poll.get_vote_permission(), poll) \
				and not poll.participants.filter(id=request.user.pk).exists() \
				and poll.end_date >= datetime.date.today():
		return vote(request, poll, url_title)

	if not poll.show_results_immediately and poll.end_date >= datetime.date.today():
		messages.info(
			request,
			_("You can not see the results of this poll right now. You have to wait until {} to see the results of this poll.".format(poll.end_date.strftime("%d. %B %Y")))
		)
		return HttpResponseRedirect(reverse('polls:index'))

	md = markdown.Markdown(safe_mode='escape', extensions=[TocExtension(baselevel=2), InternalLinksMarkdownExtension(), 'markdown.extensions.abbr', 'markdown.extensions.tables'])
	description = md.convert(poll.text + abbreviation_explanation_markdown())

	return render(
		request,
		'polls_results.html',
		{
			"document": poll,
			"description": description,
			'toc': md.toc,
			'active_page': 'view',
			'view_page': True,
			'attachments': poll.attachments.filter(no_direct_download=False).order_by('index'),
			'permission_overview': document_permission_overview(request.user, poll),
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
			return HttpResponseRedirect(reverse(poll.get_view_url_name(), args=[url_title]))
		if len(choices) > poll.max_allowed_number_of_answers:
			messages.error(request, _("You can only select up to {} options!").format(poll.max_allowed_number_of_answers))
			return HttpResponseRedirect(reverse(poll.get_view_url_name(), args=[url_title]))

		for choice_id in choices:
			choice = poll.choices.filter(id=choice_id)
			choice.update(votes=F('votes') + 1)

		poll.participants.add(request.user)
		messages.success(request, _("We've received your vote!"))
		if not poll.show_results_immediately:
			messages.info(request, _("The results of this poll will be available as from {}".format((poll.end_date + datetime.timedelta(days=1)).strftime("%d. %B %Y"))))
			return HttpResponseRedirect(reverse('polls:index'))
		return HttpResponseRedirect(reverse(poll.get_view_url_name(), args=[url_title]))

	md = markdown.Markdown(safe_mode='escape', extensions=[TocExtension(baselevel=2), InternalLinksMarkdownExtension(), 'markdown.extensions.abbr', 'markdown.extensions.tables'])
	description = md.convert(poll.text + abbreviation_explanation_markdown())

	return render(
		request,
		'polls_vote.html',
		{
			"document": poll,
			"description": description,
			'toc': md.toc,
			'active_page': 'view',
			'view_page': True,
			"widget": "checkbox" if poll.max_allowed_number_of_answers != 1 else "radio",
			'attachments': poll.attachments.filter(no_direct_download=False).order_by('index'),
			'permission_overview': document_permission_overview(request.user, poll),
		}
	)


def view(request, title):
	poll = get_object_or_404(Document, url_title=title)
	check_permissions(poll, request.user, [Poll.get_view_permission()])
	if poll.end_date < datetime.date.today() or poll.participants.filter(id=request.user.pk).exists():
		return results(request, poll, title)
	elif poll.start_date > datetime.date.today():
		messages.warning(request, _("This poll has not yet started."))
		return index(request)
	else:
		if not request.user.has_perm('polls.vote_poll', poll):
			return results(request, poll, title)
		return vote(request, poll, title)
