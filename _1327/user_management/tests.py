from django.conf import settings
from django.contrib.auth.models import Group
from django.test.utils import override_settings
from django.urls import reverse

from django_webtest import WebTest
from guardian.shortcuts import assign_perm
from guardian.utils import get_anonymous_user
from model_mommy import mommy

from _1327.information_pages.models import InformationDocument
from .models import UserProfile


class UsecaseTests(WebTest):
	extra_environ = {'HTTP_ACCEPT_LANGUAGE': 'en'}

	@classmethod
	def setUpTestData(cls):
		cls.user = mommy.make(
			UserProfile,
			username="user",
			password="pbkdf2_sha256$12000$uH9Cc7pBkaxQ$XLVGZKTbCyuDlgFQB65Mn5SAm6v/2kjpCTct1td2VTo=")
		mommy.make(UserProfile, username="noname")
		mommy.make(UserProfile, username="nofirstname", last_name="Last")
		mommy.make(UserProfile, username="nolastname", first_name="First")
		mommy.make(UserProfile, is_superuser=True, username="admin", first_name="Admin", last_name="User")

	def test_login(self):
		page = self.app.get("/login", user="")

		login_form = page.forms[0]
		login_form['username'] = "user"
		login_form['password'] = "wrong_password"
		response = login_form.submit()
		self.assertIn("Please enter a correct User name and password", response.body.decode('utf-8'))
		self.assertNotIn('has-success', response.body.decode('utf-8'))
		self.assertIn('has-error', response.body.decode('utf-8'))

		login_form = page.forms[0]
		login_form['username'] = "user"
		login_form['password'] = "test"

		self.assertEqual(login_form.submit().status_code, 302)

	def test_login_redirect_sufficient_permissions(self):
		document = mommy.make(InformationDocument)
		assign_perm(document.view_permission_name, self.user, document)

		response = self.app.get(reverse(document.get_view_url_name(), args=[document.url_title]))
		redirect_url = reverse('login') + '?next=' + reverse(document.get_view_url_name(), args=[document.url_title])
		self.assertRedirects(response, redirect_url)
		response = response.follow()

		login_form = response.forms[0]
		login_form['username'] = "user"
		login_form['password'] = "test"

		response = login_form.submit()
		self.assertRedirects(response, reverse(document.get_view_url_name(), args=[document.url_title]))
		response = response.follow()
		self.assertEqual(response.status_code, 200)

	def test_login_insufficient_permissions(self):
		document = mommy.make(InformationDocument)

		response = self.app.get(reverse(document.get_view_url_name(), args=[document.url_title]))
		redirect_url = reverse('login') + '?next=' + reverse(document.get_view_url_name(), args=[document.url_title])
		self.assertRedirects(response, redirect_url)
		response = response.follow()

		login_form = response.forms[0]
		login_form['username'] = "user"
		login_form['password'] = "test"

		response = login_form.submit()
		self.assertRedirects(response, reverse(document.get_view_url_name(), args=[document.url_title]), target_status_code=403)
		response = response.follow(status=403)
		self.assertEqual(response.status_code, 403)

	def test_name(self):
		user = UserProfile.objects.get(username='noname')
		self.assertEqual(user.get_full_name(), 'noname')
		self.assertEqual(user.get_short_name(), 'noname')

		user = UserProfile.objects.get(username='nofirstname')
		self.assertEqual(user.get_full_name(), 'Last')
		self.assertEqual(user.get_short_name(), 'nofirstname')

		user = UserProfile.objects.get(username='nolastname')
		self.assertEqual(user.get_full_name(), 'First')
		self.assertEqual(user.get_short_name(), 'First')

		user = UserProfile.objects.get(username='admin')
		self.assertEqual(user.get_full_name(), 'Admin User')
		self.assertEqual(user.get_short_name(), 'Admin')

	def test_default_group(self):
		user = mommy.make(UserProfile)
		self.assertEqual(user.groups.count(), 0)

		with self.settings(DEFAULT_USER_GROUP_NAME='Default'):
			user = mommy.make(UserProfile)
			self.assertEqual(user.groups.count(), 1)
			default_group = Group.objects.get(name='Default')
			self.assertIn(default_group, user.groups.all())


class UserImpersonationTests(WebTest):
	csrf_checks = False
	extra_environ = {'HTTP_ACCEPT_LANGUAGE': 'en'}

	@classmethod
	def setUpTestData(cls):
		cls.user = mommy.make(UserProfile, is_superuser=True)
		mommy.make(UserProfile, username='test')

	def test_view_impersonation_page(self):
		response = self.app.get(reverse('view_as'), user=self.user)
		self.assertEqual(response.status_code, 200)

		form = response.forms['user_impersonation_form']
		options = [option[-1] for option in form['username'].options]
		self.assertIn('AnonymousUser', options)
		for user in UserProfile.objects.all():
			self.assertIn(user.username, options)

	def test_view_impersonation_list_no_superuser(self):
		user = mommy.make(UserProfile)
		response = self.app.get(reverse('view_as'), user=user, expect_errors=True)
		self.assertEqual(response.status_code, 403)

	def test_impersonate_any_user(self):
		users = list(UserProfile.objects.all().exclude(username=self.user.username))
		users.append(get_anonymous_user())

		for user in users:
			response = self.app.post('/hijack/{user_id}/'.format(user_id=user.id), user=self.user)
			self.assertRedirects(response, reverse('index'))
			response = response.follow()
			self.assertEqual(response.status_code, 200)

			self.assertIn("{username}".format(username=user.get_full_name()), response.body.decode('utf-8'))

	def test_impersonate_as_user(self):
		users = list(UserProfile.objects.all().exclude(username=self.user.username))
		users.append(get_anonymous_user())

		for user in users:
			response = self.app.post('/hijack/{user_id}/'.format(user_id=user.id), user=user)
			self.assertRedirects(response, reverse('admin:login') + '?next=/hijack/{user_id}/'.format(user_id=user.id))

	def test_impersonate_wrong_url(self):
		user = UserProfile.objects.get(username='test')

		response = self.app.post('/hijack/{email}/'.format(email=user.email), user=self.user, expect_errors=True)
		self.assertEqual(response.status_code, 400)

		response = self.app.post('/hijack/{username}/'.format(username=user.username), user=self.user, expect_errors=True)
		self.assertEqual(response.status_code, 400)


class _1327AuthenticationBackendTests(WebTest):

	csrf_checks = False
	extra_environ = {'HTTP_ACCEPT_LANGUAGE': 'en'}

	@classmethod
	def setUpTestData(cls):
		cls.document = mommy.make(InformationDocument)
		cls.user = mommy.make(UserProfile)

	def test_anonymous_fallback_if_user_has_no_permissions(self):
		anonymous_user = get_anonymous_user()
		anonymous_groups = anonymous_user.groups.all()
		for group in anonymous_groups:
			assign_perm(self.document.view_permission_name, group, self.document)

		response = self.app.get(reverse(self.document.get_view_url_name(), args=[self.document.url_title]), user=self.user)
		self.assertEqual(response.status_code, 200)

	def test_anonymous_fallback_without_anonymous_permission(self):
		for group in Group.objects.all().exclude(name=settings.ANONYMOUS_GROUP_NAME):
			assign_perm(self.document.view_permission_name, group, self.document)

		response = self.app.get(reverse(self.document.get_view_url_name(), args=[self.document.url_title]), expect_errors=True, user=self.user)
		self.assertEqual(response.status_code, 403)

	def test_anonymous_fallback_not_used_if_user_has_permission(self):
		group = mommy.make(Group)
		self.user.groups.add(group)
		self.user.save()

		assign_perm(self.document.view_permission_name, group, self.document)

		response = self.app.get(reverse(self.document.get_view_url_name(), args=[self.document.url_title]), user=self.user)
		self.assertEqual(response.status_code, 200)


@override_settings(ANONYMOUS_IP_RANGE_GROUPS={'8.0.0.0/8': 'university_group'})
class _1327AuthenticationBackendUniversityNetworkTests(WebTest):

	csrf_checks = False
	extra_environ = {'HTTP_ACCEPT_LANGUAGE': 'en'}

	@classmethod
	def setUpTestData(cls):
		cls.document = mommy.make(InformationDocument)
		cls.university_group = mommy.make(Group, name='university_group')

	def test_university_network_fallback_no_access(self):
		# check that user is not allowed to view the document if he is not in the university network
		assign_perm(self.document.view_permission_name, self.university_group, self.document)

		response = self.app.get(reverse(self.document.get_view_url_name(), args=[self.document.url_title]))
		redirect_url = reverse('login') + '?next=' + reverse(self.document.get_view_url_name(), args=[self.document.url_title])
		self.assertRedirects(response, redirect_url)

	def test_university_network_fallback_access_granted(self):
		# check that user can see the document if he is in the university network
		assign_perm(self.document.view_permission_name, self.university_group, self.document)

		# mimic that the user is in the university network
		request_meta = {'REMOTE_ADDR': '8.0.0.1'}

		response = self.app.get(reverse(self.document.get_view_url_name(), args=[self.document.url_title]), extra_environ=request_meta)
		self.assertEqual(response.status_code, 200)

	def test_university_network_fallback_university_network_no_access(self):
		# mimic that the user is in the university network
		request_meta = {'REMOTE_ADDR': '8.0.0.1'}

		response = self.app.get(
			reverse(self.document.get_view_url_name(), args=[self.document.url_title]),
			extra_environ=request_meta,
		)
		redirect_url = reverse('login') + '?next=' + reverse(self.document.get_view_url_name(), args=[self.document.url_title])
		self.assertRedirects(response, redirect_url)
