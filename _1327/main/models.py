from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils.translation import ugettext_lazy as _


class UserManager(BaseUserManager):
	def create_user(self, username, password=None, email=None, first_name=None, last_name=None):
		user = self.model(
			username=username,
			email=self.normalize_email(email),
			first_name=first_name,
			last_name=last_name
		)
		user.set_password(password)
		user.save()
		return user

	def create_superuser(self, username, password, email=None, first_name=None, last_name=None):
		user = self.create_user(
			username=username,
			password=password, 
			email=email, 
			first_name=first_name, 
			last_name=last_name
		)
		user.is_superuser = True
		user.is_staff = True
		user.save()
		return user


class UserProfile(AbstractBaseUser):
	username = models.CharField(max_length=255, unique=True, verbose_name=_('username'))
	email = models.EmailField(max_length=255, blank=True, null=True, verbose_name=_('email address'))
	first_name = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("first name"))
	last_name = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("last name"))
	is_active = models.BooleanField(default=True)
	is_staff = models.BooleanField(default=False)
	is_superuser = models.BooleanField(default=False)
	# last_login = models.DateTimeField()
	# date_joined = models.DateTimeField()

	USERNAME_FIELD = 'username'
	REQUIRED_FIELDS = []

	objects = UserManager()

	def get_full_name(self):
		return first_name + ' ' + last_name

	def get_short_name(self):
		return first_name
