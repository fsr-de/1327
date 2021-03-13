from django.forms import Form, EmailField


class TencaSubscriptionForm(Form):
	email = EmailField()
