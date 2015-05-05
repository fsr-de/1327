from django_webtest import WebTest

from .models import UserProfile


class UsecaseTests(WebTest):
	fixtures = ['usecase-tests']
	extra_environ = {'HTTP_ACCEPT_LANGUAGE': 'en'}

	def test_login(self):
		page = self.app.get(("/login"), user="")

		login_form = page.forms[0]
		login_form['username'] = "user"
		login_form['password'] = "wrong_password"
		self.assertIn("Please enter a correct username and password", login_form.submit())

		login_form = page.forms[0]
		login_form['username'] = "user"
		login_form['password'] = "test"

		self.assertEqual(login_form.submit().status_code, 302)

	def test_name(self):
		user = UserProfile.objects.get(username='noname')
		self.assertEqual(user.get_full_name(), 'noname')
		self.assertEqual(user.get_short_name(), 'noname')

		user = UserProfile.objects.get(username='nofirstname')
		self.assertEqual(user.get_full_name(), 'nofirstname')
		self.assertEqual(user.get_short_name(), 'nofirstname')

		user = UserProfile.objects.get(username='nolastname')
		self.assertEqual(user.get_full_name(), 'nolastname')
		self.assertEqual(user.get_short_name(), 'First')

		user = UserProfile.objects.get(username='admin')
		self.assertEqual(user.get_full_name(), 'Admin User')
		self.assertEqual(user.get_short_name(), 'Admin')
