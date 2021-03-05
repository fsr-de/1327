from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.conf import settings
from django.core.asgi import get_asgi_application
from django.urls import path

from _1327.documents.consumers import PreviewConsumer


websocket_urlpatterns = [
	path("{preview_url}/<hash_value>".format(preview_url=settings.PREVIEW_URL.lstrip('/')), PreviewConsumer.as_asgi()),
]


application = ProtocolTypeRouter({
	'http': get_asgi_application(),
	'websocket': AuthMiddlewareStack(
		URLRouter(
			websocket_urlpatterns
		)
	)
})
