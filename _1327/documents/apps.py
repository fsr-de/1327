from django.apps import AppConfig

class DocumentConfig(AppConfig):
	name = '_1327.documents'

	def ready(self):
		import _1327.documents.signals
