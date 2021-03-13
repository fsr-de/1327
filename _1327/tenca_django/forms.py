from django.forms import Form, EmailField, CharField


class TencaSubscriptionForm(Form):
	email = EmailField()


class TencaNewListForm(Form):
	list_name = CharField()
