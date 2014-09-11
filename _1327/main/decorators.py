from django.contrib import auth
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User

def login_required(func):
    def check_user(user):
        return user.is_authenticated()
    return user_passes_test(check_user)(func)


def staff_required(func):
    def check_user(user):
        if not user.is_authenticated():
            return False
        return user.is_staff
    return user_passes_test(check_user)(func)