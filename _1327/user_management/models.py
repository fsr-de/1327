from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.translation import ugettext_lazy as _


class UserManager(BaseUserManager):
	def create_user(self, username, password=None, email=None, first_name=None, last_name=None):
		if not username:
			raise ValueError(_('Users must have a username'))

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
		user.is_admin = True
		user.save()
		return user


class UserProfile(AbstractBaseUser, PermissionsMixin):
	username = models.CharField(max_length=255, unique=True, verbose_name=_('User name'))
	email = models.EmailField(max_length=255, blank=True, null=True, verbose_name=_('Email address'))
	first_name = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("First name"))
	last_name = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Last name"))
	is_active = models.BooleanField(default=True)
	is_admin = models.BooleanField(default=False)

	USERNAME_FIELD = 'username'
	REQUIRED_FIELDS = []

	objects = UserManager()

	def get_full_name(self):
		if self.first_name and self.last_name:
			return self.first_name + ' ' + self.last_name
		return self.username

	def get_short_name(self):
		if self.first_name:
			return self.first_name
		return self.username

	def __str__(self):
		return self.get_full_name();

	def is_staff(self):
		return self.is_admin;

	def has_perm(self, perm, obj=None):
		"Does the user have a specific permission?"
		# Simplest possible answer: Yes, always
		return self.is_admin

	def has_module_perms(self, app_label):
		"Does the user have permissions to view the app `app_label`?"
		# Simplest possible answer: Yes, always
		return self.is_admin
