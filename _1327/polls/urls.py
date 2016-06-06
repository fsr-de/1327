from django.conf.urls import patterns, url


urlpatterns = patterns('_1327.polls.views',  # noqa
	url(r"^$", "list", name="list"),
)
