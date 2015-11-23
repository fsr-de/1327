import datetime

from django.core.urlresolvers import reverse
from django.test import TestCase
from django_webtest import WebTest
from guardian.shortcuts import assign_perm
from model_mommy import mommy

from _1327.polls.models import Poll, Choice
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

	def test_view_with_insufficient_permissions(self):
		response = self.app.get(reverse('polls:results', args=[self.poll.id]), expect_errors=True)
		self.assertEqual(response.status_code, 403)

	def test_view_result_without_vote(self):
		response = self.app.get(reverse('polls:results', args=[self.poll.id]), user=self.user)
		self.assertRedirects(response, reverse('polls:vote', args=[self.poll.id]))

	def test_view_after_vote(self):
		self.poll.participants.add(self.user)

		response = self.app.get(reverse('polls:results', args=[self.poll.id]), user=self.user)
		self.assertEqual(response.status_code, 200)

		for choice in self.poll.choices.all():
			self.assertIn(choice.text.encode('utf-8'), response.body)
			self.assertIn(str(choice.percentage()).encode('utf-8'), response.body)
			self.assertIn(str(choice.votes).encode('utf-8'), response.body)

	def test_view_with_description_of_poll(self):
		self.poll.description = b"a nice description"
		self.poll.participants.add(self.user)
		self.poll.save()

		response = self.app.get(reverse('polls:results', args=[self.poll.id]), user=self.user)
		self.assertEqual(response.status_code, 200)
		self.assertIn(self.poll.description, response.body)

	def test_view_before_poll_has_started(self):
		self.poll.start_date += datetime.timedelta(weeks=1)
		self.poll.save()

		response = self.app.get(reverse('polls:results', args=[self.poll.id]), user=self.user, expect_errors=True)
		self.assertEqual(response.status_code, 404)


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
		response = self.app.get(reverse('polls:vote', args=[self.poll.id]), expect_errors=True)
		self.assertEqual(response.status_code, 403)

		user = mommy.make(UserProfile)
		assign_perm(Poll.VIEW_PERMISSION_NAME, user, self.poll)

		response = self.app.get(reverse('polls:vote', args=[self.poll.id]), user=user, expect_errors=True)
		self.assertEqual(response.status_code, 403)
		response = self.app.post(reverse('polls:vote', args=[self.poll.id]), user=user, expect_errors=True)
		self.assertEqual(response.status_code, 403)

	def test_vote_with_sufficient_permissions(self):
		response = self.app.get(reverse('polls:vote', args=[self.poll.id]), user=self.user)
		self.assertEqual(response.status_code, 200)

		user = mommy.make(UserProfile)
		assign_perm(Poll.VIEW_PERMISSION_NAME, user, self.poll)
		assign_perm('change_poll', user, self.poll)
		user.save()
		response = self.app.get(reverse('polls:vote', args=[self.poll.id]), user=user)
		self.assertEqual(response.status_code, 200)

	def test_vote_poll_finished(self):
		self.poll.end_date = datetime.date.today() - datetime.timedelta(days=1)
		self.poll.save()

		response = self.app.get(reverse('polls:vote', args=[self.poll.id]), user=self.user)
		self.assertRedirects(response, reverse('polls:results', args=[self.poll.id]))

	def test_vote_poll_already_voted(self):
		self.poll.participants.add(self.user)
		self.poll.save()

		response = self.app.get(reverse('polls:vote', args=[self.poll.id]), user=self.user)
		self.assertRedirects(response, reverse('polls:results', args=[self.poll.id]))
		response = self.app.post(reverse('polls:vote', args=[self.poll.id]), user=self.user)
		self.assertRedirects(response, reverse('polls:results', args=[self.poll.id]))

	def test_start_vote_multiple_choice_poll(self):
		self.poll.max_allowed_number_of_answers = 2
		self.poll.save()

		response = self.app.get(reverse('polls:vote', args=[self.poll.id]), user=self.user)
		self.assertEqual(response.status_code, 200)
		self.assertIn(b"checkbox", response.body)
		self.assertNotIn(b"radio", response.body)

	def test_start_vote_single_choice_poll(self):
		self.poll.max_allowed_number_of_answers = 1
		self.poll.save()

		response = self.app.get(reverse('polls:vote', args=[self.poll.id]), user=self.user)
		self.assertEqual(response.status_code, 200)
		self.assertIn(b"radio", response.body)
		self.assertNotIn(b"checkbox", response.body)

	def test_choices_in_response(self):
		response = self.app.get(reverse('polls:vote', args=[self.poll.id]), user=self.user)
		self.assertEqual(response.status_code, 200)
		for choice in self.poll.choices.all():
			self.assertIn(choice.text.encode('utf-8'), response.body)

	def test_vote_without_submitting_a_choice(self):
		response = self.app.post(reverse('polls:vote', args=[self.poll.id]), user=self.user)
		self.assertRedirects(response, reverse('polls:vote', args=[self.poll.id]))

	def test_vote_single_choice_submitting_more_than_one_choice(self):
		self.poll.max_allowed_number_of_answers = 1
		self.poll.save()

		data = []
		for choice in self.poll.choices.all():
			data.append(('choice', choice.id))

		response = self.app.post(reverse('polls:vote', args=[self.poll.id]), params=data, user=self.user)
		self.assertRedirects(response, reverse('polls:vote', args=[self.poll.id]))

	def test_vote_single_choice_correctly(self):
		self.poll.max_allowed_number_of_answers = 1
		self.poll.save()

		choice = self.poll.choices.first()
		data = [('choice', choice.id)]
		votes = choice.votes
		response = self.app.post(reverse('polls:vote', args=[self.poll.id]), params=data, user=self.user)
		self.assertEqual(response.status_code, 302)
		choice = self.poll.choices.first()
		self.assertEqual(choice.votes, votes + 1)
		self.assertEqual(self.poll.participants.count(), 1)
		self.assertRedirects(response, reverse('polls:results', args=[self.poll.id]))

	def test_vote_multiple_choice_correctly(self):
		self.poll.max_allowed_number_of_answers = self.poll.choices.count()
		self.poll.save()
		data = []
		votes = []
		for choice in self.poll.choices.all():
			data.append(('choice', choice.id))
			votes.append(choice.votes)

		response = self.app.post(reverse('polls:vote', args=[self.poll.id]), params=data, user=self.user)
		self.assertEqual(response.status_code, 302)
		for i, choice in enumerate(self.poll.choices.all()):
			self.assertEqual(choice.votes, votes[i] + 1)

		self.assertEqual(self.poll.participants.count(), 1)
		self.assertRedirects(response, reverse('polls:results', args=[self.poll.id]))

	def test_view_before_poll_has_started(self):
		self.poll.start_date += datetime.timedelta(weeks=1)
		self.poll.save()

		response = self.app.get(reverse('polls:vote', args=[self.poll.id]), user=self.user, expect_errors=True)
		self.assertEqual(response.status_code, 404)
