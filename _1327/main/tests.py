from django.test import RequestFactory, TestCase
from model_mommy import mommy

from .context_processors import mark_selected
from .models import MenuItem


class TestMenuProcessor(TestCase):

	def test_mark_selected(self):
		rf = RequestFactory()
		request = rf.get('/this_is_a_page_that_most_certainly_does_not_exist.html')

		menu_item = mommy.make(MenuItem)
		try:
			mark_selected(request, menu_item)
		except AttributeError:
			self.fail("mark_selected() raises an AttributeError")
