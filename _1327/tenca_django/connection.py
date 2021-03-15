import tenca.settings
from django.conf import settings as django_settings

tenca.settings.load_from_module(django_settings)

import tenca.connection

connection = tenca.connection.Connection()
