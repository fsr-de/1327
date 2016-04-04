from django.core.urlresolvers import reverse
from django_webtest import WebTest
from model_mommy import mommy

from _1327.minutes.models import MinutesDocument
from _1327.user_management.models import UserProfile


class TestEditor(WebTest):
	csrf_checks = False

	def setUp(self):
		num_participants = 8

		self.user = mommy.make(UserProfile, is_superuser=True)
		moderator = mommy.make(UserProfile)
		participants = mommy.make(UserProfile, _quantity=num_participants)
		self.document = mommy.make(MinutesDocument, participants=participants, moderator=moderator)

	def test_get_editor(self):
		"""
		Test if the edit page shows the correct content
		"""
		response = self.app.get(reverse('documents:edit', args=[self.document.url_title]), expect_errors=True)
		self.assertEqual(response.status_code, 403)  # test anonymous user cannot access page

		response = self.app.get(reverse('documents:edit', args=[self.document.url_title]), user=self.user)
		self.assertEqual(response.status_code, 200)

		form = response.forms[0]
		self.assertEqual(form.get('title').value, self.document.title)
		self.assertEqual(form.get('text').value, self.document.text)
		self.assertEqual(int(form.get('moderator').value), self.document.moderator.id)
		self.assertEqual([int(id) for id in form.get('participants').value], [participant.id for participant in self.document.participants.all()])
