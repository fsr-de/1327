import re
from django.conf import settings
from django.contrib.auth.models import Group

from django.core.urlresolvers import reverse
from django.test import RequestFactory, TestCase
from django_webtest import WebTest
from guardian.shortcuts import assign_perm, remove_perm
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

		self.staff_group = Group.objects.get(name=settings.STAFF_GROUP_NAME)
		self.root_user.groups.add(self.staff_group)
		self.user.groups.add(self.staff_group)

		self.root_menu_item = mommy.make(MenuItem)
		self.sub_item = mommy.make(MenuItem, parent=self.root_menu_item)
		self.sub_sub_item = mommy.make(MenuItem, parent=self.sub_item)

		assign_perm(self.sub_item.change_children_permission_name, self.user, self.sub_item)
		assign_perm(self.sub_item.view_permission_name, self.user, self.sub_item)

	def test_visit_menu_item_page(self):
		user = mommy.make(UserProfile)

		response = self.app.get(reverse('menu_items_index'), user=user, status=403)
		self.assertEqual(response.status_code, 403)

		assign_perm(self.root_menu_item.change_children_permission_name, user, self.root_menu_item)
		response = self.app.get(reverse('menu_items_index'), user=user)
		self.assertEqual(response.status_code, 200)
		self.assertIn(self.root_menu_item.title, response.body.decode('utf-8'))

	def test_create_menu_item_as_superuser_no_document_and_link(self):
		menu_item_count = MenuItem.objects.count()

		response = self.app.get(reverse('menu_item_create'), user=self.root_user)
		self.assertEqual(response.status_code, 200)
		self.assertIn("Link", response.body.decode('utf-8'))

		form = response.form
		form['group'].select(text=self.staff_group.name)

		response = form.submit()
		self.assertEqual(200, response.status_code)
		self.assertIn('You must select a document or link', response.body.decode('utf-8'))
		self.assertEqual(MenuItem.objects.count(), menu_item_count)

	def test_create_menu_item_as_superuser_document_and_link(self):
		menu_item_count = MenuItem.objects.count()
		document = mommy.make(InformationDocument)

		response = self.app.get(reverse('menu_item_create'), user=self.root_user)
		form = response.form
		form['link'] = 'polls:index'
		form['document'].select(text=document.title)
		form['group'].select(text=self.staff_group.name)

		response = form.submit()
		self.assertEqual(200, response.status_code)
		self.assertIn('You are only allowed to define one of document and link', response.body.decode('utf-8'))
		self.assertEqual(MenuItem.objects.count(), menu_item_count)

	def test_create_menu_item_as_superuser_with_link(self):
		menu_item_count = MenuItem.objects.count()

		response = self.app.get(reverse('menu_item_create'), user=self.root_user)
		form = response.form
		form['title'] = 'test title'
		form['link'] = 'polls:index'
		form['group'].select(text=self.staff_group.name)

		response = form.submit().follow()
		self.assertEqual(200, response.status_code)
		self.assertIn("Successfully created menu item.", response.body.decode('utf-8'))
		self.assertEqual(MenuItem.objects.count(), menu_item_count + 1)

	def test_create_menu_item_as_superuser_with_link_and_param(self):
		menu_item_count = MenuItem.objects.count()

		response = self.app.get(reverse('menu_item_create'), user=self.root_user)
		form = response.form
		form['title'] = 'test title'
		form['link'] = 'minutes:list?{}'.format(self.staff_group.id)
		form['group'].select(text=self.staff_group.name)

		response = form.submit().maybe_follow()
		self.assertEqual(200, response.status_code)
		self.assertIn("Successfully created menu item.", response.body.decode('utf-8'))
		self.assertEqual(MenuItem.objects.count(), menu_item_count + 1)

	def test_create_menu_item_as_superuser_wrong_link(self):
		menu_item_count = MenuItem.objects.count()

		response = self.app.get(reverse('menu_item_create'), user=self.root_user)
		form = response.form
		form['title'] = 'test title'
		form['link'] = 'polls:index?kekse?kekse2'
		form['group'].select(text=self.staff_group.name)

		response = form.submit().maybe_follow()
		self.assertEqual(200, response.status_code)
		self.assertIn('This link is not valid.', response.body.decode('utf-8'))
		self.assertEqual(MenuItem.objects.count(), menu_item_count)

	def test_create_menu_item_as_superuser_wrong_link_2(self):
		menu_item_count = MenuItem.objects.count()

		response = self.app.get(reverse('menu_item_create'), user=self.root_user)
		form = response.form
		form['title'] = 'test title'
		form['link'] = 'www.example.com'
		form['group'].select(text=self.staff_group.name)

		response = form.submit().maybe_follow()
		self.assertEqual(200, response.status_code)
		self.assertIn('This link is not valid.', response.body.decode('utf-8'))
		self.assertEqual(MenuItem.objects.count(), menu_item_count)

	def test_create_menu_item_as_superuser_with_document(self):
		menu_item_count = MenuItem.objects.count()
		document = mommy.make(InformationDocument)

		response = self.app.get(reverse('menu_item_create'), user=self.root_user)
		form = response.form
		form['title'] = 'test title'
		form['document'].select(text=document.title)
		form['group'].select(text=self.staff_group.name)

		response = form.submit().follow()
		self.assertEqual(200, response.status_code)
		self.assertIn("Successfully created menu item.", response.body.decode('utf-8'))
		self.assertEqual(MenuItem.objects.count(), menu_item_count + 1)

	def test_create_menu_item_as_normal_user(self):
		response = self.app.get(reverse('menu_item_create'), user=self.user)
		self.assertEqual(response.status_code, 200)
		self.assertNotIn("Link", response.body.decode('utf-8'))

	def test_create_menu_item_as_normal_user_no_document_and_link(self):
		menu_item_count = MenuItem.objects.count()

		response = self.app.get(reverse('menu_item_create'), user=self.user)
		form = response.form
		form['group'].select(text=self.staff_group.name)

		response = form.submit()
		self.assertEqual(200, response.status_code)
		self.assertIn('You must select a document', response.body.decode('utf-8'))
		self.assertEqual(MenuItem.objects.count(), menu_item_count)

	def test_create_menu_item_as_normal_user_with_document(self):
		menu_item_count = MenuItem.objects.count()
		document = mommy.make(InformationDocument)

		response = self.app.get(reverse('menu_item_create'), user=self.user)
		form = response.form
		form['title'] = 'test title'
		form['document'].select(text=document.title)
		form['group'].select(text=self.staff_group.name)
		form['parent'].select(text=self.sub_item.title)

		response = form.submit().maybe_follow()
		self.assertEqual(200, response.status_code)
		self.assertIn("Successfully created menu item.", response.body.decode('utf-8'))
		self.assertEqual(MenuItem.objects.count(), menu_item_count + 1)

	def test_create_menu_item_as_normal_user_with_document_without_parent(self):
		menu_item_count = MenuItem.objects.count()
		document = mommy.make(InformationDocument)

		response = self.app.get(reverse('menu_item_create'), user=self.user)
		form = response.form
		form['title'] = 'test title'
		form['document'].select(text=document.title)
		form['group'].select(text=self.staff_group.name)

		response = form.submit().maybe_follow()
		self.assertEqual(200, response.status_code)
		self.assertIn("This field is required", response.body.decode('utf-8'))
		self.assertEqual(MenuItem.objects.count(), menu_item_count)

	def test_create_menu_wrong_group(self):
		menu_item_count = MenuItem.objects.count()
		document = mommy.make(InformationDocument)
		group = mommy.make(Group)

		response = self.app.get(reverse('menu_item_create'), user=self.user)
		form = response.form
		form['title'] = 'test title'
		form['document'].select(text=document.title)
		form['group'].force_value(group.id)

		response = form.submit().maybe_follow()
		self.assertEqual(200, response.status_code)
		self.assertIn("Select a valid choice. That choice is not one of the available choices.", response.body.decode('utf-8'))
		self.assertEqual(MenuItem.objects.count(), menu_item_count)

	def test_change_menu_items(self):
		for user in [self.root_user, self.user]:
			response = self.app.get(reverse('menu_items_index'), user=user)
			self.assertEqual(response.status_code, 200)

			response_text = response.body.decode('utf-8')
			self.assertIn(self.root_menu_item.title, response_text)
			self.assertIn(self.sub_item.title, response_text)
			self.assertIn(self.sub_sub_item.title, response_text)

	def test_possibility_to_change_root_item(self):
		response = self.app.get(reverse('menu_items_index'), user=self.user)
		self.assertEqual(response.status_code, 200)
		self.assertNotIn(reverse('menu_item_edit', args=[self.root_menu_item.id]), response.body.decode('utf-8'))

		response = self.app.get(reverse('menu_items_index'), user=self.root_user)
		self.assertEqual(response.status_code, 200)
		self.assertIn(reverse('menu_item_edit', args=[self.root_menu_item.id]), response.body.decode('utf-8'))

	def test_find_root_menu_items(self):
		sub_item = mommy.make(MenuItem, parent=self.root_menu_item)
		sub_sub_item = mommy.make(MenuItem, parent=self.sub_item)

		menu_items = [sub_sub_item, self.sub_sub_item, sub_item]
		root_menu_items = find_root_menu_items(menu_items)

		self.assertCountEqual(root_menu_items, [self.root_menu_item])

	def test_set_edit_permission_on_menu_item(self):
		response = self.app.get(reverse('menu_items_index'), user=self.user)
		self.assertEqual(response.status_code, 200)
		self.assertNotIn(reverse('menu_item_edit', args=[self.sub_item.id]), response.body.decode('utf-8'))
		self.assertIn(reverse('menu_item_edit', args=[self.sub_sub_item.id]), response.body.decode('utf-8'))

		assign_perm(self.sub_item.edit_permission_name, self.user, self.sub_item)

		response = self.app.get(reverse('menu_items_index'), user=self.user)
		self.assertEqual(response.status_code, 200)
		self.assertIn(reverse('menu_item_edit', args=[self.sub_item.id]), response.body.decode('utf-8'))
		self.assertIn(reverse('menu_item_edit', args=[self.sub_sub_item.id]), response.body.decode('utf-8'))

	def test_change_parent_without_edit_permission(self):
		extra_sub_item = mommy.make(MenuItem, parent=self.sub_item)

		response = self.app.get(reverse('menu_items_index'), user=self.user)
		self.assertEqual(response.status_code, 200)
		self.assertIn(reverse('menu_item_edit', args=[extra_sub_item.id]), response.body.decode('utf-8'))

		extra_sub_item.parent = self.root_menu_item
		extra_sub_item.save()

		response = self.app.get(reverse('menu_items_index'), user=self.user)
		self.assertEqual(response.status_code, 200)
		self.assertNotIn(reverse('menu_item_edit', args=[extra_sub_item.id]), response.body.decode('utf-8'))

	def test_change_parent_with_edit_permission(self):
		extra_sub_item = mommy.make(MenuItem, parent=self.sub_item)
		assign_perm(extra_sub_item.edit_permission_name, self.user, extra_sub_item)

		response = self.app.get(reverse('menu_items_index'), user=self.user)
		self.assertEqual(response.status_code, 200)
		self.assertIn(reverse('menu_item_edit', args=[extra_sub_item.id]), response.body.decode('utf-8'))

		extra_sub_item.parent = self.root_menu_item
		extra_sub_item.save()

		response = self.app.get(reverse('menu_items_index'), user=self.user)
		self.assertEqual(response.status_code, 200)
		self.assertIn(reverse('menu_item_edit', args=[extra_sub_item.id]), response.body.decode('utf-8'))

	def test_menu_item_ordering(self):
		self.root_menu_item.order = 2
		self.root_menu_item.save()
		remove_perm(self.sub_item.change_children_permission_name, self.user, self.sub_item)
		self.sub_item.delete()

		mommy.make(MenuItem, order=0)
		mommy.make(MenuItem, order=1)

		menu_items = list(MenuItem.objects.filter(menu_type=MenuItem.MAIN_MENU).order_by('order'))
		for idx, item in enumerate(menu_items):
			assign_perm(item.change_children_permission_name, self.user, item)
			item.order = idx
			item.save()
		menu_items.append(MenuItem.objects.get(menu_type=MenuItem.FOOTER))

		response = self.app.get(reverse('menu_items_index'), user=self.root_user)
		response_text = response.body.decode('utf-8')

		menu_item_ids = re.findall(r"menu_item/(\d+)/edit", response_text)
		self.assertEqual(len(menu_item_ids), len(menu_items))

		for menu_item_id, menu_item in zip(menu_item_ids, menu_items):
			self.assertEqual(menu_item.id, int(menu_item_id), 'Menu Item ordering is not as expected')
