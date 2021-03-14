from django.forms import Form, EmailField, CharField, BooleanField, HiddenInput, EmailInput
from django.utils.translation import gettext as _


class TencaSubscriptionForm(Form):
	email = EmailField()


class TencaNewListForm(Form):
	list_name = CharField()


class TencaListOptionsForm(Form):
	notsubscribed_allowed_to_post = BooleanField(label=_("Not subscribed users are allowed to post."), required=False)
	replies_addressed_to_list = BooleanField(label=_("Replies are addressed to the list per default."), required=False)
	# Fields should be named according to their respective setting on the tenca list object

	def __init__(self, *args, **kwargs):
		mailing_list = kwargs.pop("mailing_list")
		super().__init__(*args, **kwargs)
		for key, field in self.fields.items():
			field.initial = getattr(mailing_list, key)


class TencaMemberEditForm(Form):
	email = EmailField(widget=EmailInput(attrs={"class": "form-control-plaintext", "readonly": True}))

