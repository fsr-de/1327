from django_webtest import WebTest
from model_mommy import mommy

from .models import UserProfile


class UsecaseTests(WebTest):
	extra_environ = {'HTTP_ACCEPT_LANGUAGE': 'de'}

	def setUp(self):
		self.user = mommy.make(
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
		self.assertIn("Bitte gib einen korrekten Benutzernamen und Passwort ein.", login_form.submit())

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
