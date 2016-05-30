import datetime

from django.core.urlresolvers import reverse
from django.template.defaultfilters import floatformat
from django.test import TestCase
from django_webtest import WebTest
from guardian.shortcuts import assign_perm
from model_mommy import mommy

from _1327.polls.models import Choice, Poll
from _1327.user_management.models import UserProfile


class PollModelTests(TestCase):

	def test_percentage(self):
		num_votes = 10
		num_choices = 3
		num_participants = 5

		user = mommy.make(UserProfile, _quantity=num_participants)
		poll = mommy.make(Poll, participants=user)

		mommy.make(Choice, poll=poll, _quantity=num_choices, votes=num_votes)

		expected_percentage = num_votes * 100 / num_participants
		for choice in poll.choices.all():
			self.assertAlmostEqual(choice.percentage(), expected_percentage, 2)

	def test_percentage_with_no_participants(self):
		poll = mommy.make(Poll)

		num_choices = 3
		mommy.make(Choice, poll=poll, _quantity=num_choices, votes=0)

		expected_percentage = 0
		for choice in poll.choices.all():
			self.assertAlmostEqual(choice.percentage(), expected_percentage, 2)


class PollViewTests(WebTest):

	def setUp(self):
		self.user = mommy.make(UserProfile, is_superuser=True)
		self.poll = mommy.make(
			Poll,
			start_date=datetime.date.today(),
			end_date=datetime.date.today() + datetime.timedelta(days=3),
		)
		mommy.make(
			Choice,
			poll=self.poll,
			_quantity=3,
		)

	def test_view_all_running_poll_with_insufficient_permissions(self):
		response = self.app.get(reverse('polls:list'))
		self.assertEqual(response.status_code, 200)
		self.assertIn(b"There are no polls you can vote for.", response.body)
		self.assertIn(b"There are no results you can see.", response.body)

	def test_view_all_running_poll_with_sufficient_permissions(self):
		response = self.app.get(reverse('polls:list'), user=self.user)
		self.assertEqual(response.status_code, 200)
		self.assertIn(self.poll.title.encode('utf-8'), response.body)
		self.assertIn(b"There are no results you can see.", response.body)

	def test_view_all_running_and_not_running(self):
		finished_poll = mommy.make(
			Poll,
			start_date=datetime.date.today() - datetime.timedelta(days=10),
			end_date=datetime.date.today() - datetime.timedelta(days=1),
		)

		response = self.app.get(reverse('polls:list'), user=self.user)
		self.assertEqual(response.status_code, 200)
		self.assertIn(self.poll.title.encode('utf-8'), response.body)
		self.assertIn(finished_poll.title.encode('utf-8'), response.body)

	def test_view_all_already_participated(self):
		self.poll.participants.add(self.user)
		self.poll.save()

		response = self.app.get(reverse('polls:list'), user=self.user)
		self.assertEqual(response.status_code, 200)
		self.assertIn(b"There are no polls you can vote for.", response.body)
		self.assertIn(self.poll.title.encode('utf-8'), response.body)

	def test_view_all_future_poll(self):
		self.poll.start_date += datetime.timedelta(days=1)
		self.poll.save()

		response = self.app.get(reverse('polls:list'))
		self.assertEqual(response.status_code, 200)
		self.assertIn(b"There are no polls you can vote for.", response.body)
		self.assertIn(b"There are no results you can see.", response.body)

	def test_create_poll(self):
		response = self.app.get(reverse('documents:create', args=['poll']), user=self.user)
		self.assertEqual(response.status_code, 200)

		form = response.forms['document-form']
		form['choices-0-description'] = 'test description'
		form['choices-0-index'] = 0
		form['choices-0-text'] = 'test choice'
		form['title'] = 'TestPoll'
		form['text'] = 'Sample Text'
		form['max_allowed_number_of_answers'] = 1
		form['start_date'] = '2016-01-01'
		form['end_date'] = '2088-01-01'
		form['comment'] = 'sample comment'

		response = form.submit()
		self.assertEqual(response.status_code, 302)

		poll = Poll.objects.get(title='TestPoll')
		self.assertEqual(poll.choices.count(), 1)

	def test_create_poll_user_has_no_permission(self):
		user = mommy.make(UserProfile)

		response = self.app.get(reverse('documents:create', args=['poll']), user=user, expect_errors=True)
		self.assertEqual(response.status_code, 403)

		response = self.app.post(reverse('documents:create', args=['poll']), user=user, expect_errors=True)
		self.assertEqual(response.status_code, 403)

	def test_edit_poll(self):
		response = self.app.get(reverse('documents:edit', args=[self.poll.url_title]), user=self.user)
		self.assertEqual(response.status_code, 200)

		choice_text = 'test choice'
		choice_description = 'test description'
		poll_description = 'Description'

		form = response.forms['document-form']
		form['choices-3-description'] = choice_description
		form['choices-3-index'] = 3
		form['choices-3-text'] = choice_text
		form['choices-0-text'] = choice_text
		form['text'] = poll_description
		form['comment'] = 'sample comment'

		response = form.submit()
		self.assertEqual(response.status_code, 302)

		poll = Poll.objects.get(id=self.poll.id)
		self.assertEqual(poll.text, poll_description)
		self.assertEqual(poll.choices.count(), 4)
		self.assertEqual(poll.choices.first().text, choice_text)
		self.assertEqual(poll.choices.last().text, choice_text)
		self.assertEqual(poll.choices.last().description, choice_description)

	def test_edit_poll_delete_choice(self):
		response = self.app.get(reverse('documents:edit', args=[self.poll.url_title]), user=self.user)
		self.assertEqual(response.status_code, 200)

		form = response.forms['document-form']
		form['choices-0-DELETE'] = True
		form['comment'] = 'sample comment'

		response = form.submit()
		self.assertEqual(response.status_code, 302)

		poll = Poll.objects.get(id=self.poll.id)
		self.assertEqual(poll.choices.count(), 2)

	def test_edit_poll_user_has_no_permission(self):
		user = mommy.make(UserProfile)

		response = self.app.get(reverse('documents:edit', args=[self.poll.url_title]), user=user, expect_errors=True)
		self.assertEqual(response.status_code, 403)

		response = self.app.post(reverse('documents:edit', args=[self.poll.url_title]), user=user, expect_errors=True)
		self.assertEqual(response.status_code, 403)


class PollResultTests(WebTest):

	def setUp(self):
		self.user = mommy.make(UserProfile, is_superuser=True)
		self.poll = mommy.make(
			Poll,
			start_date=datetime.date.today(),
			end_date=datetime.date.today() + datetime.timedelta(days=3),
		)
		mommy.make(
			Choice,
			poll=self.poll,
			votes=10,
			_quantity=3,
		)

	def assign_vote_perm(self, user, obj):
		assign_perm('polls.{vote}'.format(vote=Poll.VOTE_PERMISSION_NAME), user, obj)
		user.save()

	def assign_view_perm(self, user, obj):
		assign_perm('polls.{view}'.format(view=Poll.VIEW_PERMISSION_NAME), user, obj)
		user.save()

	def assign_view_vote_perms(self, user, obj):
		self.assign_view_perm(user, obj)
		self.assign_vote_perm(user, obj)

	def test_view_with_insufficient_permissions(self):
		response = self.app.get(reverse('polls:results', args=[self.poll.url_title]), expect_errors=True)
		self.assertEqual(response.status_code, 403)

	def test_view_result_without_vote(self):
		user = mommy.make(UserProfile)
		self.assign_view_vote_perms(user, self.poll)
		response = self.app.get(reverse('polls:results', args=[self.poll.url_title]), user=user)
		self.assertRedirects(response, reverse('polls:vote', args=[self.poll.url_title]))

	def test_view_after_vote(self):
		user = mommy.make(UserProfile)
		self.assign_view_vote_perms(user, self.poll)
		self.poll.participants.add(user)

		response = self.app.get(reverse('polls:results', args=[self.poll.url_title]), user=user)
		self.assertEqual(response.status_code, 200)

		for choice in self.poll.choices.all():
			self.assertIn(choice.text.encode('utf-8'), response.body)
			self.assertIn(floatformat(choice.percentage()).encode('utf-8'), response.body)
			self.assertIn(str(choice.votes).encode('utf-8'), response.body)

	def test_view_with_description_of_poll(self):
		user = mommy.make(UserProfile)
		self.assign_view_vote_perms(user, self.poll)
		self.poll.text = b"a nice description"
		self.poll.participants.add(user)
		self.poll.save()

		response = self.app.get(reverse('polls:results', args=[self.poll.url_title]), user=user)
		self.assertEqual(response.status_code, 200)
		self.assertIn(self.poll.text, response.body)

	def test_view_before_poll_has_started(self):
		user = mommy.make(UserProfile)
		self.assign_view_vote_perms(user, self.poll)
		self.poll.start_date += datetime.timedelta(weeks=1)
		self.poll.save()

		response = self.app.get(reverse('polls:results', args=[self.poll.url_title]), user=user, expect_errors=True)
		self.assertEqual(response.status_code, 404)

	def test_view_poll_without_vote_permission(self):
		user = mommy.make(UserProfile)
		self.assign_view_perm(user, self.poll)

		response = self.app.get(reverse('polls:results', args=[self.poll.url_title]), user=user, expect_errors=True)
		self.assertEqual(response.status_code, 200)

	def test_vote_poll_without_vote_permission(self):
		user = mommy.make(UserProfile)
		self.assign_view_perm(user, self.poll)

		response = self.app.get(reverse('polls:vote', args=[self.poll.url_title]), user=user, expect_errors=True)
		self.assertEqual(response.status_code, 403)


class PollVoteTests(WebTest):
	csrf_checks = False

	def setUp(self):
		self.user = mommy.make(UserProfile, is_superuser=True)
		self.poll = mommy.make(
			Poll,
			start_date=datetime.date.today(),
			end_date=datetime.date.today() + datetime.timedelta(days=3),
		)
		mommy.make(
			Choice,
			poll=self.poll,
			votes=10,
			_quantity=3,
		)

	def test_vote_with_insufficient_permissions(self):
		response = self.app.get(reverse('polls:vote', args=[self.poll.url_title]), expect_errors=True)
		self.assertEqual(response.status_code, 403)

		user = mommy.make(UserProfile)
		assign_perm(Poll.VIEW_PERMISSION_NAME, user, self.poll)

		response = self.app.get(reverse('polls:vote', args=[self.poll.url_title]), user=user, expect_errors=True)
		self.assertEqual(response.status_code, 403)
		response = self.app.post(reverse('polls:vote', args=[self.poll.url_title]), user=user, expect_errors=True)
		self.assertEqual(response.status_code, 403)

	def test_vote_with_sufficient_permissions(self):
		response = self.app.get(reverse('polls:vote', args=[self.poll.url_title]), user=self.user)
		self.assertEqual(response.status_code, 200)

		user = mommy.make(UserProfile)
		assign_perm(Poll.VIEW_PERMISSION_NAME, user, self.poll)
		assign_perm('vote_poll', user, self.poll)
		user.save()
		response = self.app.get(reverse('polls:vote', args=[self.poll.url_title]), user=user)
		self.assertEqual(response.status_code, 200)

	def test_vote_poll_finished(self):
		self.poll.end_date = datetime.date.today() - datetime.timedelta(days=1)
		self.poll.save()

		response = self.app.get(reverse('polls:vote', args=[self.poll.url_title]), user=self.user)
		self.assertRedirects(response, reverse('polls:results', args=[self.poll.url_title]))

	def test_vote_poll_already_voted(self):
		self.poll.participants.add(self.user)
		self.poll.save()

		response = self.app.get(reverse('polls:vote', args=[self.poll.url_title]), user=self.user)
		self.assertRedirects(response, reverse('polls:results', args=[self.poll.url_title]))
		response = self.app.post(reverse('polls:vote', args=[self.poll.url_title]), user=self.user)
		self.assertRedirects(response, reverse('polls:results', args=[self.poll.url_title]))

	def test_start_vote_multiple_choice_poll(self):
		self.poll.max_allowed_number_of_answers = 2
		self.poll.save()

		response = self.app.get(reverse('polls:vote', args=[self.poll.url_title]), user=self.user)
		self.assertEqual(response.status_code, 200)
		self.assertIn(b"checkbox", response.body)
		self.assertNotIn(b"radio", response.body)

	def test_start_vote_single_choice_poll(self):
		self.poll.max_allowed_number_of_answers = 1
		self.poll.save()

		response = self.app.get(reverse('polls:vote', args=[self.poll.url_title]), user=self.user)
		self.assertEqual(response.status_code, 200)
		self.assertIn(b"radio", response.body)
		self.assertNotIn(b"checkbox", response.body)

	def test_choices_in_response(self):
		response = self.app.get(reverse('polls:vote', args=[self.poll.url_title]), user=self.user)
		self.assertEqual(response.status_code, 200)
		for choice in self.poll.choices.all():
			self.assertIn(choice.text.encode('utf-8'), response.body)

	def test_vote_without_submitting_a_choice(self):
		response = self.app.post(reverse('documents:view', args=[self.poll.url_title]), user=self.user)
		self.assertRedirects(response, reverse('documents:view', args=[self.poll.url_title]))

	def test_vote_single_choice_submitting_more_than_one_choice(self):
		self.poll.max_allowed_number_of_answers = 1
		self.poll.save()

		data = []
		for choice in self.poll.choices.all():
			data.append(('choice', choice.id))

		response = self.app.post(reverse('documents:view', args=[self.poll.url_title]), params=data, user=self.user)
		self.assertRedirects(response, reverse('documents:view', args=[self.poll.url_title]))

	def test_vote_single_choice_correctly(self):
		self.poll.max_allowed_number_of_answers = 1
		self.poll.save()

		choice = self.poll.choices.first()
		data = [('choice', choice.id)]
		votes = choice.votes
		response = self.app.post(reverse('polls:vote', args=[self.poll.url_title]), params=data, user=self.user)
		self.assertEqual(response.status_code, 302)
		choice = self.poll.choices.first()
		self.assertEqual(choice.votes, votes + 1)
		self.assertEqual(self.poll.participants.count(), 1)
		self.assertRedirects(response, reverse('polls:results', args=[self.poll.url_title]))

	def test_vote_multiple_choice_correctly(self):
		self.poll.max_allowed_number_of_answers = self.poll.choices.count()
		self.poll.save()
		data = []
		votes = []
		for choice in self.poll.choices.all():
			data.append(('choice', choice.id))
			votes.append(choice.votes)

		response = self.app.post(reverse('polls:vote', args=[self.poll.url_title]), params=data, user=self.user)
		self.assertEqual(response.status_code, 302)
		for i, choice in enumerate(self.poll.choices.all()):
			self.assertEqual(choice.votes, votes[i] + 1)

		self.assertEqual(self.poll.participants.count(), 1)
		self.assertRedirects(response, reverse('polls:results', args=[self.poll.url_title]))

	def test_view_before_poll_has_started(self):
		self.poll.start_date += datetime.timedelta(weeks=1)
		self.poll.save()

		response = self.app.get(reverse('polls:vote', args=[self.poll.url_title]), user=self.user, expect_errors=True)
		self.assertEqual(response.status_code, 404)
