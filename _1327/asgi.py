import os

from channels.routing import get_default_application

import django


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_1327.settings")
django.setup()
application = get_default_application()
