from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand

from _1327.user_management.models import UserProfile
from django.contrib.auth.models import Group, Permission

class Command(BaseCommand):
    args = ''
    help = 'Adds a helpful superuser admin/admin for development purposes'

    def handle(self, *args, **options):
        if not settings.DEBUG:
            self.stdout.write("DEBUG is disabled. Are you sure you are not running")
            if input("on a production system and want to continue? (yes/no)") != "yes":
                self.stdout.write("Aborting...")
                return

        self.stdout.write('Adding superuser admin with password admin.')

        UserProfile.objects.filter(username="admin").delete()
        user = UserProfile(username='admin', email='admin@example.com', password='admin', is_superuser=True)
        user.save()

        Group.objects.filter(name="Admin").delete()
        group = Group(name="Admin")
        group.save()
        group.user_set.add(user)

        for permission in Permission.objects.filter(codename__in=[
                "add_minutesdocument",
                "add_informationdocument",
                "add_poll",
            ]):
            permission.group_set.add(group)

        self.stdout.write('Done.')
