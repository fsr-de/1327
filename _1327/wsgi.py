"""
WSGI config for _1327 project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/howto/deployment/wsgi/
"""

import sys

sys.stderr = sys.stdout

import os

pwd = os.path.dirname(os.path.abspath(__file__))
projectdir = os.path.join(pwd, "..")
os.chdir(projectdir)
sys.path = [projectdir] + sys.path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_1327.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
