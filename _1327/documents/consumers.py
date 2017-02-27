from channels import Group


def get_group_name(id):
	return '_'.join(['preview', id])


def send_preview(message, id):
	Group(get_group_name(id)).send({
		"text": message.content['text'],
	})


def ws_add(message):
	message.reply_channel.send({"accept": True})
	group_name = message.content['path'].replace('/ws/', '').replace('/', '_')
	Group(group_name).add(message.reply_channel)


def ws_disconnect(message):
	group_name = message.content['path'].replace('/ws/', '').replace('/', '_')
	Group(group_name).discard(message.reply_channel)
