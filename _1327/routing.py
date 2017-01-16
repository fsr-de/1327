from channels.routing import route

from _1327.documents.consumers import send_preview, ws_add, ws_disconnect

channel_routing = [
	route("websocket.connect", ws_add),
	route("send_preview", send_preview),
	route("websocket.disconnect", ws_disconnect),
]
