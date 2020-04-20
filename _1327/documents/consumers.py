from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer


class PreviewConsumer(WebsocketConsumer):

	def connect(self):
		self.group_name = self.scope['url_route']['kwargs']['hash_value']
		async_to_sync(self.channel_layer.group_add)(
			self.group_name,
			self.channel_name,
		)

		self.accept()

	def disconnect(self, messsage, **kwargs):
		async_to_sync(self.channel_layer.group_discard)(
			self.group_name,
			self.channel_name,
		)

	def update_preview(self, event):
		self.send(text_data=event['message'])
