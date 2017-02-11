from channels import Group


def send_preview(message):
	Group('preview').send({
		"text": message.content['text'],
	})


def ws_add(message):
	print("new user")
	message.reply_channel.send({"accept": True})
	Group("preview").add(message.reply_channel)


def ws_disconnect(message):
	Group("preview").discard(message.reply_channel)
