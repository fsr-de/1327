import os
import subprocess
import sys

from django.core.management import execute_from_command_line
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    args = ''
    help = 'Stop apache and execute "runserver 0.0.0.0:80"'

    def handle(self, *args, **options):
        if os.getuid() != 0:
            print('Error: The "run" command must be executed with root privileges.')
            sys.exit(1)
        subprocess.call("service apache2 stop", shell=True)
        print('Executing "manage.py runserver 0.0.0.0:80"')
        sys.argv = ["manage.py", "runserver", "0.0.0.0:80"]
        execute_from_command_line(sys.argv)
