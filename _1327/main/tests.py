from django.core.urlresolvers import reverse
from django.test import RequestFactory, TestCase
from django_webtest import WebTest
from guardian.shortcuts import assign_perm
from guardian.utils import get_anonymous_user
from model_mommy import mommy

from _1327.information_pages.models import InformationDocument
from _1327.main.utils import find_root_menu_items
from _1327.minutes.models import MinutesDocument
from _1327.user_management.models import UserProfile
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


class MainPageTests(WebTest):

	def test_main_page_no_page_set(self):
		response = self.app.get(reverse('index'))
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'index.html')

	def test_main_page_information_page_set(self):
		document = mommy.make(InformationDocument)
		assign_perm(InformationDocument.VIEW_PERMISSION_NAME, get_anonymous_user(), document)
		with self.settings(MAIN_PAGE_ID=document.id):
			response = self.app.get(reverse('index')).follow()
			self.assertEqual(response.status_code, 200)
			self.assertTemplateUsed(response, 'documents_base.html')

			response = self.app.get(reverse('index') + '/').follow()
			self.assertEqual(response.status_code, 200)
			self.assertTemplateUsed(response, 'documents_base.html')

	def test_main_page_minutes_document_set(self):
		document = mommy.make(MinutesDocument)
		assign_perm(MinutesDocument.VIEW_PERMISSION_NAME, get_anonymous_user(), document)
		with self.settings(MAIN_PAGE_ID=document.id):
			response = self.app.get(reverse('index')).follow()
			self.assertEqual(response.status_code, 200)
			self.assertTemplateUsed(response, 'documents_base.html')


class MenuItemTests(WebTest):

	def setUp(self):
		self.root_user = mommy.make(UserProfile, is_superuser=True)
		self.user = mommy.make(UserProfile)

		self.root_menu_item = mommy.make(MenuItem)
		self.sub_item = mommy.make(MenuItem, parent=self.root_menu_item)
		self.sub_sub_item = mommy.make(MenuItem, parent=self.sub_item)

		assign_perm(self.sub_item.change_children_permission_name, self.user, self.sub_item)
		assign_perm(self.sub_item.view_permission_name, self.user, self.sub_item)

	def test_change_menu_items(self):
		for user in [self.root_user, self.user]:
			response = self.app.get(reverse('menu_items_index'), user=user)
			self.assertEqual(response.status_code, 200)

			response_text = response.body.decode('utf-8')
			self.assertIn(self.root_menu_item.title, response_text)
			self.assertIn(self.sub_item.title, response_text)
			self.assertIn(self.sub_sub_item.title, response_text)

	def test_find_root_menu_items(self):
		sub_item = mommy.make(MenuItem, parent=self.root_menu_item)
		sub_sub_item = mommy.make(MenuItem, parent=self.sub_item)

		menu_items = [sub_sub_item, self.sub_sub_item, sub_item]
		root_menu_items = find_root_menu_items(menu_items)

		self.assertCountEqual(root_menu_items, [self.root_menu_item])
