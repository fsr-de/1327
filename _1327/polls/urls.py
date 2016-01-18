from django.conf.urls import patterns, url


urlpatterns = patterns('_1327.polls.views',  # noqa
	url(r"^$", "list", name="list"),
	url(r"create$", "create", name="create"),
	url(r"(?P<poll_id>\d+)/edit", "edit", name="edit"),
	url(r"(?P<poll_id>\d+)/results$", "results", name="results"),
	url(r"(?P<poll_id>\d+)/vote$", "vote", name="vote"),
)
