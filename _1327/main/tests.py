from django_webtest import WebTest
import webtest

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
