from django.conf.urls import patterns, url


urlpatterns = patterns('_1327.polls.views',  # noqa
	url(r"^$", "list", name="list"),
	url(r"(?P<url_title>[\w-]+)/results$", "results", name="results"),
	url(r"(?P<url_title>[\w-]+)/vote$", "vote", name="vote"),
)
