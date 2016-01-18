import datetime

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.forms import inlineformset_factory
from django.http import Http404, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _

from _1327.polls.forms import ChoiceForm, PollForm
from _1327.polls.models import Choice, Poll
from _1327.user_management.shortcuts import get_object_or_error


def list(request):
	running_polls = []
	finished_polls = []
	# do not show polls that start in the future and that a user is not allowed to see
	for poll in Poll.objects.filter(start_date__lte=datetime.date.today()):
		if request.user.has_perm(Poll.VIEW_PERMISSION_NAME):
			if datetime.date.today() <= poll.end_date and not poll.participants.filter(id=request.user.pk).exists():
				running_polls.append(poll)
			else:
				finished_polls.append(poll)

	return render(
		request,
		'polls_index.html',
		{
			"running_polls": running_polls,
			"finished_polls": finished_polls,
		}
	)


def create(request, poll=None, url=None, success_message=_("Successfully created new Poll.")):
	if not request.user.has_perm("polls.add_poll"):
		return HttpResponseForbidden()

	InlineChoiceFormset = inlineformset_factory(Poll, Choice, form=ChoiceForm, extra=2 if poll is None else 1, can_delete=True)

	form = PollForm(request.POST or None, instance=poll)
	formset = InlineChoiceFormset(request.POST or None, instance=poll)
	if form.is_valid() and formset.is_valid():
		poll = form.save()
		choices = formset.save(commit=False)

		for choice_to_delete in formset.deleted_objects:
			choice_to_delete.delete()

		for choice in choices:
			choice.poll = poll
			choice.save()

		messages.success(request, success_message)
		return HttpResponseRedirect(reverse('polls:list'))

	return render(
		request,
		"polls_create_poll.html",
		{
			'url': url if url is not None else reverse('polls:create'),
			'form': form,
			'formset': formset,
		}
	)


def edit(request, poll_id):
	poll = get_object_or_error(Poll, request.user, ['polls.change_poll'], id=poll_id)
	return create(request, poll=poll, url=reverse('polls:edit', args=[poll_id]), success_message=_("Successfully updated Poll."))


def results(request, poll_id):
	poll = get_object_or_error(Poll, request.user, ['polls.view_poll'], id=poll_id)

	if poll.start_date > datetime.date.today():
		# poll is not open
		raise Http404

	if not poll.participants.filter(id=request.user.pk).exists() and poll.end_date > datetime.date.today():
		messages.info(request, _("You have to vote before you can see the results!"))
		return HttpResponseRedirect(reverse('polls:vote', args=[poll.id]))

	return render(
		request,
		'polls_results.html',
		{
			"poll": poll,
		}
	)


def vote(request, poll_id):
	poll = get_object_or_error(Poll, request.user, ['polls.view_poll', 'polls.change_poll'], id=poll_id)

	if poll.start_date > datetime.date.today():
		# poll is not open
		raise Http404

	if poll.end_date < datetime.date.today() or poll.participants.filter(id=request.user.pk).exists():
		messages.info(request, _("You can not vote for polls that are already finished, or that you have already voted for!"))
		return HttpResponseRedirect(reverse('polls:results', args=[poll_id]))

	if request.method == 'POST':
		choices = request.POST.getlist('choice')
		if len(choices) == 0:
			messages.error(request, _("You must select one Choice at least!"))
			return HttpResponseRedirect(reverse('polls:vote', args=[poll_id]))
		if len(choices) > poll.max_allowed_number_of_answers:
			messages.error(request, _("You can only select up to {} options!").format(poll.max_allowed_number_of_answers))
			return HttpResponseRedirect(reverse('polls:vote', args=[poll_id]))

		for choice_id in choices:
			choice = poll.choices.get(id=choice_id)
			choice.votes += 1
			choice.save()

		poll.participants.add(request.user)
		messages.success(request, _("We've received your vote!"))
		return HttpResponseRedirect(reverse('polls:results', args=[poll_id]))

	return render(
		request,
		'polls_vote.html',
		{
			"poll": poll,
			"widget": "checkbox" if poll.max_allowed_number_of_answers != 1 else "radio"
		}
	)
